from typing import Optional
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.report import MissionReportSummary
from app.services.report_service import ReportService
from app.services.simulation_engine import simulator

router = APIRouter(prefix="/v1/reports", tags=["Reports & Exports"])

@router.get("/mission-summary", response_model=MissionReportSummary)
def get_mission_summary(db: Session = Depends(get_db)):
    return ReportService.get_mission_summary(db)

@router.get("/commands/csv")
def get_commands_csv(run_id: Optional[str] = None, db: Session = Depends(get_db)):
    effective_run_id = run_id or simulator.active_run_id
    csv_str = ReportService.export_commands_csv(db, run_id=effective_run_id)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=aurora_commands_{effective_run_id or 'all'}.csv"},
    )
