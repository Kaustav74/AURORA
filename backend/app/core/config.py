import os
from typing import List
from pydantic import BaseModel, Field

class Settings(BaseModel):
    PROJECT_NAME: str = "AURORA - Spacecraft Mission Operations Simulator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./aurora.db")
    )
    ALLOW_DEV_FAULT_INJECTION: bool = Field(
        default_factory=lambda: os.getenv("ALLOW_DEV_FAULT_INJECTION", "false").lower() in ("true", "1", "yes")
    )
    DEFAULT_SIMULATION_CADENCE_HZ: float = Field(
        default_factory=lambda: float(os.getenv("DEFAULT_SIMULATION_CADENCE_HZ", "1.0"))
    )
    OVERHEAT_THRESHOLD_C: float = Field(
        default_factory=lambda: float(os.getenv("OVERHEAT_THRESHOLD_C", "75.0"))
    )
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

settings = Settings()
