from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class SimulationStatus(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"

class SimulationStartRequest(BaseModel):
    name: str = Field(default="Mission Alpha", description="Simulation run name")
    seed: int = Field(default=42, description="Random seed for determinism")
    cadence_hz: float = Field(default=1.0, ge=0.1, le=50.0, description="Simulation step rate in Hz")
    config: Optional[Dict[str, Any]] = None

class SimulationStatusResponse(BaseModel):
    run_id: Optional[str] = None
    name: Optional[str] = None
    status: SimulationStatus
    seed: int
    cadence_hz: float
    sim_time_seconds: float
    start_wall_time: Optional[datetime] = None
    updated_wall_time: Optional[datetime] = None
    is_active: bool = False

class FaultInjectionRequest(BaseModel):
    fault_type: str = Field(..., description="Fault class, e.g., OVERHEATING, COMM_LOSS, LOW_BATTERY")
    intensity: float = Field(default=1.0, description="Fault magnitude or severity multiplier")
    duration_seconds: Optional[float] = Field(default=None, description="Fault duration, or persistent if null")
    target_value: Optional[float] = Field(default=None, description="Explicit target override (e.g., 82.5 for temperature)")
