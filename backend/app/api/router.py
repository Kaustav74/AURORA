from fastapi import APIRouter
from app.api.routes import (
    health,
    simulation,
    telemetry,
    state,
    commands,
    incidents,
    events,
    mission_plans,
    scenarios,
    health_intel,
    systems_engineering,
    reports,
    websocket,
)

api_router = APIRouter()

# Health endpoints (both /api/health and /api/v1/metadata)
api_router.include_router(health.router)
api_router.include_router(simulation.router)
api_router.include_router(telemetry.router)
api_router.include_router(state.router)
api_router.include_router(commands.router)
api_router.include_router(incidents.router)
api_router.include_router(events.router)
api_router.include_router(mission_plans.router)
api_router.include_router(scenarios.router)
api_router.include_router(health_intel.router)
api_router.include_router(systems_engineering.router)
api_router.include_router(reports.router)
api_router.include_router(websocket.router)
