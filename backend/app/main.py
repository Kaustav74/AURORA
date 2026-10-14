import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db import init_db, SessionLocal
from app.services.scenario_service import ScenarioService
from app.services.systems_engineering_service import SystemsEngineeringService
from app.services.simulation_engine import simulator
from app.schemas.simulation import SimulationStatus
from app.api.router import api_router

setup_logging()

async def simulation_ticker():
    """
    Background simulation clock loop.
    Advances active simulation runs at configured cadence.
    """
    logger.info("Simulation background clock ticker started.")
    while True:
        try:
            if simulator.status == SimulationStatus.RUNNING:
                # Step simulation by 1 / cadence_hz
                step_dt = 1.0 / simulator.cadence_hz if simulator.cadence_hz > 0 else 1.0
                db = SessionLocal()
                try:
                    simulator.step(db=db, dt=step_dt)
                finally:
                    db.close()
                await asyncio.sleep(step_dt)
            else:
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in simulation ticker: {e}")
            await asyncio.sleep(1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    logger.info("Initializing AURORA Database...")
    init_db()
    db = SessionLocal()
    try:
        ScenarioService.seed_default_scenarios(db)
        SystemsEngineeringService.seed_initial_records(db)
        # Initialize default simulation run if none exists
        if not simulator.active_run_id:
            simulator.start(db=db, name="AURORA Orbital Pass 1", seed=42, cadence_hz=settings.DEFAULT_SIMULATION_CADENCE_HZ)
    finally:
        db.close()

    # Launch background clock
    ticker_task = asyncio.create_task(simulation_ticker())
    yield
    # Shutdown:
    ticker_task.cancel()
    try:
        await ticker_task
    except asyncio.CancelledError:
        pass
    logger.info("AURORA backend shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Software-only spacecraft mission-operations simulator, telemetry engine and systems-engineering workbench (Educational / Portfolio Simulation Only).",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API endpoints under /api
app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {
        "service": "Project AURORA Mission Operations Simulator",
        "documentation": "/docs",
        "health": "/api/health",
        "disclaimer": "SIMULATION SOFTWARE ONLY - NOT CONNECTED TO REAL SPACECRAFT OR FLIGHT HARDWARE",
    }
