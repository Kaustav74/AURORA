from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ScenarioDefinitionCreate(BaseModel):
    id: str = Field(..., description="Unique scenario ID, e.g. SCN-NOMINAL")
    name: str
    description: str
    seed: int = 42
    initial_config: Dict[str, Any] = Field(default_factory=dict)
    fault_schedule: List[Dict[str, Any]] = Field(default_factory=list)
    expected_outcomes: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"

class ScenarioDefinitionResponse(BaseModel):
    id: str
    name: str
    description: str
    seed: int
    initial_config: Dict[str, Any]
    fault_schedule: List[Dict[str, Any]]
    expected_outcomes: Dict[str, Any]
    version: str

class ScenarioRunResponse(BaseModel):
    id: str
    scenario_id: str
    run_id: Optional[str]
    status: str
    seed: int
    observed_outcomes: Optional[Dict[str, Any]] = None
    pass_fail: Optional[str] = None
    deviations: Optional[List[str]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
