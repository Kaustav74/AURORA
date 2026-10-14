from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.state import SpacecraftMode

class TelemetryResponse(BaseModel):
    id: Optional[int] = None
    run_id: str
    timestamp_sim: float
    timestamp_wall: datetime
    mode: SpacecraftMode
    temperature_c: float
    battery_soc_pct: float
    bus_voltage_v: float
    current_draw_a: float
    comm_status: str  # NOMINAL, DEGRADED, LOST
    signal_quality_pct: float
    attitude_error_deg: float
    angular_rate_deg_s: float
    storage_used_pct: float
    sensors_valid: bool
    metadata: Optional[Dict[str, Any]] = None
    is_stale: bool = False

class TelemetryFilter(BaseModel):
    run_id: Optional[str] = None
    start_sim_time: Optional[float] = None
    end_sim_time: Optional[float] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
