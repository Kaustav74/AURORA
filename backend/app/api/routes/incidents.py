import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.incident import (
    IncidentResponse,
    IncidentAcknowledgeRequest,
    IncidentResolveRequest,
    IncidentStatus,
    IncidentSeverity,
)
from app.services.incident_service import IncidentService
from app.services.simulation_engine import simulator

router = APIRouter(prefix="/v1/incidents", tags=["Faults & Incidents"])

@router.get("", response_model=List[IncidentResponse])
def get_incidents(
    run_id: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    records = IncidentService.get_incidents(
        db=db,
        run_id=run_id,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    res = []
    for r in records:
        snap = json.loads(r.telemetry_snapshot_json) if r.telemetry_snapshot_json else None
        res.append(
            IncidentResponse(
                id=r.id,
                run_id=r.run_id,
                fault_type=r.fault_type,
                severity=IncidentSeverity(r.severity),
                status=IncidentStatus(r.status),
                summary=r.summary,
                details=r.details,
                first_seen_sim=r.first_seen_sim,
                last_seen_sim=r.last_seen_sim,
                acknowledged_at=r.acknowledged_at,
                acknowledged_by=r.acknowledged_by,
                resolved_at=r.resolved_at,
                resolution_reason=r.resolution_reason,
                telemetry_snapshot=snap,
            )
        )
    return res

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident_by_id(incident_id: str, db: Session = Depends(get_db)):
    r = IncidentService.get_incident_by_id(db, incident_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")
    snap = json.loads(r.telemetry_snapshot_json) if r.telemetry_snapshot_json else None
    return IncidentResponse(
        id=r.id,
        run_id=r.run_id,
        fault_type=r.fault_type,
        severity=IncidentSeverity(r.severity),
        status=IncidentStatus(r.status),
        summary=r.summary,
        details=r.details,
        first_seen_sim=r.first_seen_sim,
        last_seen_sim=r.last_seen_sim,
        acknowledged_at=r.acknowledged_at,
        acknowledged_by=r.acknowledged_by,
        resolved_at=r.resolved_at,
        resolution_reason=r.resolution_reason,
        telemetry_snapshot=snap,
    )

@router.post("/{incident_id}/acknowledge", response_model=IncidentResponse)
def acknowledge_incident(incident_id: str, req: IncidentAcknowledgeRequest, db: Session = Depends(get_db)):
    try:
        r = IncidentService.acknowledge_incident(db, incident_id, acknowledged_by=req.acknowledged_by)
        snap = json.loads(r.telemetry_snapshot_json) if r.telemetry_snapshot_json else None
        return IncidentResponse(
            id=r.id,
            run_id=r.run_id,
            fault_type=r.fault_type,
            severity=IncidentSeverity(r.severity),
            status=IncidentStatus(r.status),
            summary=r.summary,
            details=r.details,
            first_seen_sim=r.first_seen_sim,
            last_seen_sim=r.last_seen_sim,
            acknowledged_at=r.acknowledged_at,
            acknowledged_by=r.acknowledged_by,
            resolved_at=r.resolved_at,
            resolution_reason=r.resolution_reason,
            telemetry_snapshot=snap,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(incident_id: str, req: IncidentResolveRequest, db: Session = Depends(get_db)):
    try:
        r = IncidentService.resolve_incident(db, incident_id, reason=req.reason, resolved_by=req.resolved_by)
        snap = json.loads(r.telemetry_snapshot_json) if r.telemetry_snapshot_json else None
        return IncidentResponse(
            id=r.id,
            run_id=r.run_id,
            fault_type=r.fault_type,
            severity=IncidentSeverity(r.severity),
            status=IncidentStatus(r.status),
            summary=r.summary,
            details=r.details,
            first_seen_sim=r.first_seen_sim,
            last_seen_sim=r.last_seen_sim,
            acknowledged_at=r.acknowledged_at,
            acknowledged_by=r.acknowledged_by,
            resolved_at=r.resolved_at,
            resolution_reason=r.resolution_reason,
            telemetry_snapshot=snap,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
