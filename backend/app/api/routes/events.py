import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.event import EventResponse
from app.services.event_service import EventService
from app.services.simulation_engine import simulator

router = APIRouter(prefix="/v1/events", tags=["Event Log & Replay"])

@router.get("", response_model=List[EventResponse])
def get_events(
    run_id: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    records = EventService.get_events(
        db=db,
        run_id=run_id,
        category=category,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    res = []
    for r in records:
        details = json.loads(r.details_json) if r.details_json else None
        res.append(
            EventResponse(
                id=r.id,
                run_id=r.run_id,
                event_type=r.event_type,
                category=r.category,
                severity=r.severity,
                message=r.message,
                details=details,
                timestamp_sim=r.timestamp_sim,
                timestamp_wall=r.timestamp_wall,
            )
        )
    return res

@router.get("/replay/{run_id}")
def get_event_replay_timeline(run_id: str, db: Session = Depends(get_db)):
    timeline = EventService.get_replay_timeline(db, run_id)
    return {
        "run_id": run_id,
        "total_events": len(timeline),
        "timeline": timeline,
    }

@router.get("/replay/{run_id}/frames")
def get_event_replay_frames(run_id: str, db: Session = Depends(get_db)):
    return EventService.get_replay_frames(db, run_id)

@router.get("/export/csv")
def export_events_csv(run_id: Optional[str] = None, db: Session = Depends(get_db)):
    effective_run_id = run_id or simulator.active_run_id
    csv_str = EventService.export_events_csv(db=db, run_id=effective_run_id)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=aurora_events_{effective_run_id or 'all'}.csv"},
    )

@router.get("/{event_id}", response_model=EventResponse)
def get_event_by_id(event_id: str, db: Session = Depends(get_db)):
    r = EventService.get_event_by_id(db, event_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event '{event_id}' not found.")
    details = json.loads(r.details_json) if r.details_json else None
    return EventResponse(
        id=r.id,
        run_id=r.run_id,
        event_type=r.event_type,
        category=r.category,
        severity=r.severity,
        message=r.message,
        details=details,
        timestamp_sim=r.timestamp_sim,
        timestamp_wall=r.timestamp_wall,
    )
