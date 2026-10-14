from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class MissionReportSummary(BaseModel):
    generated_at: datetime
    run_id: Optional[str] = None
    simulation_time_seconds: float
    spacecraft_mode: str
    total_telemetry_frames: int
    total_events: int
    open_incidents: int
    resolved_incidents: int
    total_commands: int
    readiness_score_pct: float
    notes: List[str]
    disclaimer: str = "AURORA EDUCATIONAL SIMULATION REPORT - NOT FOR FLIGHT OPERATIONS"
