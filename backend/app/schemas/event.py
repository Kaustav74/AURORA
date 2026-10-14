from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class EventResponse(BaseModel):
    id: str
    run_id: Optional[str] = None
    event_type: str
    category: str
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp_sim: float
    timestamp_wall: datetime

class EventFilter(BaseModel):
    run_id: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
