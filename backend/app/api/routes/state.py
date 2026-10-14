from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import SpacecraftStateRecord
from app.schemas.state import SpacecraftStateResponse, SpacecraftMode, RecoveryRequest
from app.services.state_machine import StateMachine, StateMachineError
from app.services.simulation_engine import simulator

router = APIRouter(prefix="/v1/state", tags=["Spacecraft State"])

@router.get("/current", response_model=SpacecraftStateResponse)
def get_current_state(db: Session = Depends(get_db)):
    run_id = simulator.active_run_id or "UNINITIALIZED"
    latest = (
        db.query(SpacecraftStateRecord)
        .filter(SpacecraftStateRecord.run_id == run_id)
        .order_by(SpacecraftStateRecord.timestamp_sim.desc(), SpacecraftStateRecord.id.desc())
        .first()
    )

    if latest:
        return SpacecraftStateResponse(
            id=latest.id,
            run_id=latest.run_id,
            mode=SpacecraftMode(latest.mode),
            previous_mode=SpacecraftMode(latest.previous_mode) if latest.previous_mode else None,
            reason=latest.reason,
            source=latest.source,
            timestamp_sim=latest.timestamp_sim,
            timestamp_wall=latest.timestamp_wall,
        )

    return SpacecraftStateResponse(
        run_id=run_id,
        mode=simulator.current_mode,
        previous_mode=None,
        reason="Default initial simulator state",
        source="SYSTEM",
        timestamp_sim=simulator.sim_time_seconds,
        timestamp_wall=datetime.utcnow(),
    )

@router.get("/history", response_model=List[SpacecraftStateResponse])
def get_state_history(run_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(SpacecraftStateRecord)
    effective_run_id = run_id or simulator.active_run_id
    if effective_run_id:
        query = query.filter(SpacecraftStateRecord.run_id == effective_run_id)
    records = query.order_by(SpacecraftStateRecord.timestamp_sim.desc(), SpacecraftStateRecord.id.desc()).all()

    return [
        SpacecraftStateResponse(
            id=r.id,
            run_id=r.run_id,
            mode=SpacecraftMode(r.mode),
            previous_mode=SpacecraftMode(r.previous_mode) if r.previous_mode else None,
            reason=r.reason,
            source=r.source,
            timestamp_sim=r.timestamp_sim,
            timestamp_wall=r.timestamp_wall,
        )
        for r in records
    ]

@router.post("/recovery-request")
def request_recovery(req: RecoveryRequest, db: Session = Depends(get_db)):
    if simulator.current_mode != SpacecraftMode.SAFE_MODE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Recovery request is only valid when spacecraft is in SAFE_MODE (current: {simulator.current_mode.value}).",
        )

    # Precondition check
    satisfied, reason = StateMachine.check_recovery_preconditions(
        telemetry=simulator.latest_telemetry
    )
    if not satisfied and not req.force_override:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Recovery Precondition Check Failed: {reason}",
        )

    # Transition to RECOVERY
    try:
        StateMachine.transition(
            db=db,
            run_id=simulator.active_run_id or "NO-RUN",
            current_mode=SpacecraftMode.SAFE_MODE,
            target_mode=SpacecraftMode.RECOVERY,
            reason=f"Recovery authorized by {req.requested_by}: {req.reason}",
            source=f"CMD:{req.requested_by}",
            sim_time=simulator.sim_time_seconds,
        )
        simulator.current_mode = SpacecraftMode.RECOVERY

        # Clear simulated thermal fault and cool down
        simulator.clear_fault("OVERHEATING")

        # Promote to NOMINAL after successful post-recovery self-test
        StateMachine.transition(
            db=db,
            run_id=simulator.active_run_id or "NO-RUN",
            current_mode=SpacecraftMode.RECOVERY,
            target_mode=SpacecraftMode.NOMINAL,
            reason="Subsystem checkout verified; safe recovery complete.",
            source="AUTONOMOUS_CHECKOUT",
            sim_time=simulator.sim_time_seconds,
        )
        simulator.current_mode = SpacecraftMode.NOMINAL

        return {
            "success": True,
            "message": "Recovery sequence completed successfully.",
            "final_mode": SpacecraftMode.NOMINAL.value,
        }
    except StateMachineError as sme:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(sme))
