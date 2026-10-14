from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class MissionTaskCreate(BaseModel):
    id: str = Field(..., description="Unique task identifier, e.g. TSK-001")
    title: str = Field(..., description="Short title")
    description: str
    priority: int = Field(default=2, ge=1, le=4, description="1=Critical, 2=High, 3=Medium, 4=Low")
    duration_minutes: int = Field(..., ge=1, description="Duration in minutes")
    earliest_start_minutes: int = Field(default=0, ge=0)
    deadline_minutes: Optional[int] = None
    dependencies: List[str] = Field(default_factory=list)
    resources: Optional[Dict[str, Any]] = None

class MissionTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    duration_minutes: Optional[int] = None
    earliest_start_minutes: Optional[int] = None
    deadline_minutes: Optional[int] = None
    dependencies: Optional[List[str]] = None
    resources: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class MissionTaskResponse(BaseModel):
    id: str
    title: str
    description: str
    priority: int
    duration_minutes: int
    earliest_start_minutes: int
    deadline_minutes: Optional[int] = None
    dependencies: List[str]
    resources: Optional[Dict[str, Any]] = None
    status: str
    scheduled_start_minutes: Optional[int] = None
    scheduled_end_minutes: Optional[int] = None
    scheduling_notes: Optional[str] = None

class ScheduleGenerateResponse(BaseModel):
    success: bool
    total_tasks: int
    scheduled_tasks: int
    unscheduled_tasks: int
    conflicts: List[str]
    makespan_minutes: int
    tasks: List[MissionTaskResponse]
