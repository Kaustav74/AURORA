from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class SpacecraftMode(str, Enum):
    STANDBY = "STANDBY"
    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    SAFE_MODE = "SAFE_MODE"
    RECOVERY = "RECOVERY"
    SIMULATION_STOPPED = "SIMULATION_STOPPED"

class SpacecraftStateResponse(BaseModel):
    id: Optional[int] = None
    run_id: str
    mode: SpacecraftMode
    previous_mode: Optional[SpacecraftMode] = None
    reason: str
    source: str
    timestamp_sim: float
    timestamp_wall: datetime

class RecoveryRequest(BaseModel):
    requested_by: str = Field(default="OPERATOR", description="Operator identifier")
    reason: str = Field(..., description="Operational justification for recovery")
    force_override: bool = Field(default=False, description="Whether to attempt emergency override (still audited)")
