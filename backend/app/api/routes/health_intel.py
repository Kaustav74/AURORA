from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.health import SpacecraftHealthOverview
from app.services.health_service import HealthService

router = APIRouter(prefix="/v1/health-intel", tags=["Health Intelligence"])

@router.get("/overview", response_model=SpacecraftHealthOverview)
def get_health_overview(run_id: Optional[str] = None, db: Session = Depends(get_db)):
    return HealthService.get_health_overview(db=db, run_id=run_id)
