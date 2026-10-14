from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class CommandType(str, Enum):
    SET_MODE = "SET_MODE"
    REQUEST_TELEMETRY = "REQUEST_TELEMETRY"
    ADJUST_PARAMETER = "ADJUST_PARAMETER"
    RECOVERY_REQUEST = "RECOVERY_REQUEST"
    RESET_FAULT = "RESET_FAULT"
    PING = "PING"

class CommandStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class CommandCreateRequest(BaseModel):
    command_type: CommandType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None
    issued_by: str = Field(default="OPERATOR")

class CommandResponse(BaseModel):
    id: str
    run_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    command_type: CommandType
    parameters: Dict[str, Any]
    issued_by: str
    status: CommandStatus
    rejection_reason: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    executed_at: Optional[datetime] = None
