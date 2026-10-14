from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class IncidentSeverity(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"

class IncidentResponse(BaseModel):
    id: str
    run_id: Optional[str] = None
    fault_type: str
    severity: IncidentSeverity
    status: IncidentStatus
    summary: str
    details: str
    first_seen_sim: float
    last_seen_sim: float
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_reason: Optional[str] = None
    telemetry_snapshot: Optional[Dict[str, Any]] = None

class IncidentAcknowledgeRequest(BaseModel):
    acknowledged_by: str = Field(default="OPERATOR")

class IncidentResolveRequest(BaseModel):
    reason: str = Field(..., description="Operational resolution justification")
    resolved_by: str = Field(default="OPERATOR")
