"""
AURORA Physics Lab - API Routes
Versioned REST endpoints under /api/v1/physics-lab
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.physics_lab_service import PhysicsLabService
from app.schemas.physics_lab import (
    PhysicsModelMetaResponse,
    CreateExperimentRequest,
    ExperimentSummaryResponse,
    ExperimentDetailResponse,
    TrajectoryResponse,
    AnomalyFindingResponse,
    UpdateAnomalyStatusRequest,
    CompareModelsRequest,
    ParameterSweepRequest,
    ParameterFitRequest,
)

router = APIRouter(prefix="/v1/physics-lab", tags=["Physics Lab"])


@router.get("/models", response_model=List[PhysicsModelMetaResponse])
def get_models():
    """List all registered physics models and their validation status."""
    return PhysicsLabService.list_models()


@router.get("/models/{model_id}", response_model=PhysicsModelMetaResponse)
def get_model(model_id: str):
    """Retrieve detailed equation provenance and parameters for a specific model."""
    meta = PhysicsLabService.get_model(model_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physics model '{model_id}' not found in registry."
        )
    return meta


@router.post("/experiments", response_model=Dict[str, Any])
def create_experiment(
    request: CreateExperimentRequest,
    db: Session = Depends(get_db)
):
    """Execute a numerical orbit propagation experiment and persist results."""
    try:
        return PhysicsLabService.create_and_run_experiment(db, request)
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Experiment propagation failed: {str(ex)}"
        )


@router.get("/experiments", response_model=List[ExperimentSummaryResponse])
def list_experiments(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """List persisted physics simulation experiments."""
    return PhysicsLabService.list_experiments(db, limit=limit, offset=offset)


@router.get("/experiments/{experiment_id}", response_model=ExperimentDetailResponse)
def get_experiment_detail(experiment_id: str, db: Session = Depends(get_db)):
    """Retrieve full details, events, and anomaly findings for an experiment."""
    exp = PhysicsLabService.get_experiment(db, experiment_id)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found."
        )
    return exp


@router.get("/experiments/{experiment_id}/trajectory", response_model=TrajectoryResponse)
def get_trajectory(experiment_id: str, db: Session = Depends(get_db)):
    """Retrieve decimated 3D trajectory frames for an experiment."""
    traj = PhysicsLabService.get_trajectory(db, experiment_id)
    if not traj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trajectory for experiment '{experiment_id}' not found."
        )
    return traj


@router.post("/experiments/compare", response_model=Dict[str, Any])
def compare_models(
    request: CompareModelsRequest,
    db: Session = Depends(get_db)
):
    """Run side-by-side simulations of multiple models from identical initial conditions."""
    try:
        return PhysicsLabService.compare_models(db, request)
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model comparison failed: {str(ex)}"
        )


@router.get("/anomalies", response_model=List[AnomalyFindingResponse])
def get_anomalies(
    experiment_id: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Search and filter detected scientific anomalies."""
    return PhysicsLabService.get_anomalies(
        db,
        experiment_id=experiment_id,
        category=category,
        severity=severity,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.post("/anomalies/{anomaly_id}/status")
def update_anomaly_status(
    anomaly_id: str,
    request: UpdateAnomalyStatusRequest,
    db: Session = Depends(get_db)
):
    """Update finding status (NEW, INVESTIGATING, REPRODUCED, RESOLVED, DISMISSED)."""
    res = PhysicsLabService.update_anomaly_status(
        db,
        anomaly_id=anomaly_id,
        status=request.status,
        resolution_notes=request.resolution_notes,
    )
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Anomaly '{anomaly_id}' not found.")
    return res


@router.post("/anomalies/{anomaly_id}/reproduce")
def reproduce_anomaly(anomaly_id: str, db: Session = Depends(get_db)):
    """Re-run the exact configuration to test anomaly reproducibility."""
    res = PhysicsLabService.reproduce_anomaly(db, anomaly_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Anomaly '{anomaly_id}' not found.")
    return res


@router.post("/anomalies/{anomaly_id}/diagnostic-run")
def diagnostic_rerun(anomaly_id: str, db: Session = Depends(get_db)):
    """Re-run simulation with 10x tighter tolerances to evaluate numerical convergence."""
    res = PhysicsLabService.diagnostic_rerun(db, anomaly_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Anomaly '{anomaly_id}' not found.")
    return res


@router.post("/sweeps")
def run_parameter_sweep(request: ParameterSweepRequest):
    """Run parameter sweep sensitivity analysis."""
    try:
        return PhysicsLabService.run_sweep(request)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))


@router.post("/fitting")
def run_parameter_fitting(request: ParameterFitRequest):
    """Perform bounded parameter estimation against target radial orbital speeds."""
    try:
        return PhysicsLabService.run_fit(request)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))


@router.get("/validation/summary")
def get_validation_summary():
    """Retrieve test matrix, analytical verification statuses, and benchmark evidence."""
    models = PhysicsLabService.list_models()
    return {
        "status": "OPERATIONAL",
        "verified_models_count": len([m for m in models if m.get("implementation_status") == "NUMERICALLY_VERIFIED"]),
        "total_models": len(models),
        "disclaimer": "SIMULATION & RESEARCH BENCHMARK ONLY - NOT CERTIFIED FOR FLIGHT OPERATIONS",
        "models": models,
    }


@router.get("/export/csv")
def export_trajectory_csv(experiment_id: str, db: Session = Depends(get_db)):
    """Export decimated trajectory time-series as CSV."""
    traj = PhysicsLabService.get_trajectory(db, experiment_id)
    if not traj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{experiment_id}' not found.")

    points = traj["points"]
    lines = [
        "t_sim_s,x_m,y_m,z_m,vx_mps,vy_mps,vz_mps,radius_m,speed_mps,specific_energy,energy_drift_rel,angular_momentum_mag,total_mass_kg,propellant_mass_kg,grav_accel_mps2,thrust_accel_mps2"
    ]
    for p in points:
        lines.append(
            f"{p['t_sim']},{p['x']},{p['y']},{p['z']},{p['vx']},{p['vy']},{p['vz']},{p['radius_m']},{p['speed_mps']},{p['specific_energy']},{p['energy_drift_rel']},{p['angular_momentum_mag']},{p['total_mass_kg']},{p['propellant_mass_kg']},{p['grav_acceleration_mps2']},{p['thrust_acceleration_mps2']}"
        )

    csv_data = "\n".join(lines)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=aurora_physics_traj_{experiment_id[:8]}.csv"},
    )
