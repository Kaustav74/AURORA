from datetime import datetime
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", tags=["Health"])
def get_health():
    return {
        "status": "HEALTHY",
        "service": "AURORA Spacecraft Mission Operations Simulator",
        "version": settings.VERSION,
        "environment": "SIMULATION_EDUCATIONAL",
        "timestamp": datetime.utcnow().isoformat(),
        "disclaimer": "SIMULATION SOFTWARE ONLY - NOT FOR FLIGHT OPERATIONS",
    }

@router.get("/v1/metadata", tags=["Metadata"])
def get_metadata():
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "overheat_threshold_c": settings.OVERHEAT_THRESHOLD_C,
        "default_cadence_hz": settings.DEFAULT_SIMULATION_CADENCE_HZ,
        "allow_dev_fault_injection": settings.ALLOW_DEV_FAULT_INJECTION,
    }
