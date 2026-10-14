from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.simulation import (
    SimulationStartRequest,
    SimulationStatusResponse,
    FaultInjectionRequest,
)
from app.services.simulation_engine import simulator
from app.core.config import settings

router = APIRouter(prefix="/v1", tags=["Simulation"])

@router.get("/simulation/status", response_model=SimulationStatusResponse)
def get_simulation_status():
    return SimulationStatusResponse(
        run_id=simulator.active_run_id,
        name=simulator.name,
        status=simulator.status,
        seed=simulator.seed,
        cadence_hz=simulator.cadence_hz,
        sim_time_seconds=round(simulator.sim_time_seconds, 2),
        start_wall_time=simulator.start_wall_time,
        is_active=(simulator.active_run_id is not None and simulator.status.value == "RUNNING"),
    )

@router.post("/simulation/start", response_model=SimulationStatusResponse)
def start_simulation(req: SimulationStartRequest, db: Session = Depends(get_db)):
    try:
        sim_run = simulator.start(
            db=db,
            name=req.name,
            seed=req.seed,
            cadence_hz=req.cadence_hz,
            config=req.config,
        )
        return SimulationStatusResponse(
            run_id=sim_run.id,
            name=sim_run.name,
            status=simulator.status,
            seed=sim_run.seed,
            cadence_hz=sim_run.cadence_hz,
            sim_time_seconds=sim_run.sim_time_seconds,
            start_wall_time=sim_run.start_wall_time,
            is_active=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/simulation/pause", response_model=SimulationStatusResponse)
def pause_simulation(db: Session = Depends(get_db)):
    try:
        simulator.pause(db)
        return get_simulation_status()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/simulation/resume", response_model=SimulationStatusResponse)
def resume_simulation(db: Session = Depends(get_db)):
    try:
        simulator.resume(db)
        return get_simulation_status()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/simulation/stop", response_model=SimulationStatusResponse)
def stop_simulation(db: Session = Depends(get_db)):
    simulator.stop(db)
    return get_simulation_status()

@router.post("/simulation/step")
def step_simulation(dt: float = 1.0, db: Session = Depends(get_db)):
    if dt < 0:
        raise HTTPException(status_code=400, detail="Time step dt must be non-negative.")
    telemetry = simulator.step(db=db, dt=dt)
    return {
        "success": True,
        "sim_time": simulator.sim_time_seconds,
        "mode": simulator.current_mode.value,
        "telemetry": telemetry,
    }

@router.post("/faults/inject")
def inject_fault(req: FaultInjectionRequest):
    if not settings.ALLOW_DEV_FAULT_INJECTION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development/test fault injection is disabled in this environment. Set ALLOW_DEV_FAULT_INJECTION=true in configuration to enable.",
        )
    simulator.inject_fault(
        fault_type=req.fault_type,
        intensity=req.intensity,
        duration_seconds=req.duration_seconds,
        target_value=req.target_value,
    )
    return {
        "status": "INJECTED",
        "fault_type": req.fault_type,
        "intensity": req.intensity,
        "target_value": req.target_value,
        "warning": "DEVELOPMENT / TEST ONLY: Active fault will alter simulated subsystem dynamics.",
    }

@router.post("/faults/clear")
def clear_fault(fault_type: str):
    if not settings.ALLOW_DEV_FAULT_INJECTION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development fault clearing is disabled in this environment.",
        )
    simulator.clear_fault(fault_type)
    return {"status": "CLEARED", "fault_type": fault_type}
