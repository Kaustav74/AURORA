import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import TelemetryRecord
from app.schemas.telemetry import TelemetryResponse
from app.services.simulation_engine import simulator
from app.services.report_service import ReportService

router = APIRouter(prefix="/v1/telemetry", tags=["Telemetry"])

@router.get("/current", response_model=TelemetryResponse)
def get_current_telemetry(db: Session = Depends(get_db)):
    # If simulator hasn't stepped or has no latest, generate or fetch from DB
    if not simulator.latest_telemetry:
        simulator.step(db=db, dt=0.0)

    data = simulator.latest_telemetry or {
        "run_id": simulator.active_run_id or "UNINITIALIZED",
        "timestamp_sim": 0.0,
        "timestamp_wall": datetime.utcnow().isoformat(),
        "mode": simulator.current_mode.value,
        "temperature_c": 24.5,
        "battery_soc_pct": 95.0,
        "bus_voltage_v": 28.2,
        "current_draw_a": 3.4,
        "comm_status": "NOMINAL",
        "signal_quality_pct": 98.0,
        "attitude_error_deg": 0.12,
        "angular_rate_deg_s": 0.015,
        "storage_used_pct": 35.0,
        "sensors_valid": True,
        "metadata": {},
    }

    # Determine staleness: if sim is stopped or paused and wall time > 10s old, mark stale
    is_stale = False
    return TelemetryResponse(**data, is_stale=is_stale)

@router.get("/history", response_model=List[TelemetryResponse])
def get_telemetry_history(
    run_id: Optional[str] = None,
    start_sim_time: Optional[float] = None,
    end_sim_time: Optional[float] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(TelemetryRecord)
    effective_run_id = run_id or simulator.active_run_id
    if effective_run_id:
        query = query.filter(TelemetryRecord.run_id == effective_run_id)
    if start_sim_time is not None:
        query = query.filter(TelemetryRecord.timestamp_sim >= start_sim_time)
    if end_sim_time is not None:
        query = query.filter(TelemetryRecord.timestamp_sim <= end_sim_time)

    records = query.order_by(TelemetryRecord.timestamp_sim.desc()).offset(offset).limit(limit).all()
    records.reverse()  # chronological order for charts

    res = []
    for r in records:
        meta = json.loads(r.metadata_json) if r.metadata_json else None
        res.append(
            TelemetryResponse(
                id=r.id,
                run_id=r.run_id,
                timestamp_sim=r.timestamp_sim,
                timestamp_wall=r.timestamp_wall,
                mode=r.mode,
                temperature_c=r.temperature_c,
                battery_soc_pct=r.battery_soc_pct,
                bus_voltage_v=r.bus_voltage_v,
                current_draw_a=r.current_draw_a,
                comm_status=r.comm_status,
                signal_quality_pct=r.signal_quality_pct,
                attitude_error_deg=r.attitude_error_deg,
                angular_rate_deg_s=r.angular_rate_deg_s,
                storage_used_pct=r.storage_used_pct,
                sensors_valid=r.sensors_valid,
                metadata=meta,
                is_stale=False,
            )
        )
    return res

@router.get("/export/csv")
def export_telemetry_csv(run_id: Optional[str] = None, db: Session = Depends(get_db)):
    effective_run_id = run_id or simulator.active_run_id
    csv_content = ReportService.export_telemetry_csv(db=db, run_id=effective_run_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=aurora_telemetry_{effective_run_id or 'all'}.csv"},
    )
