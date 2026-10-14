from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SubsystemHealth(BaseModel):
    name: str  # Thermal, Electrical/Power, Communications, ADCS, OBDH/Data
    status: str  # NOMINAL, DEGRADED, CRITICAL
    score_pct: float
    summary: str
    active_warnings: List[str]

class SubsystemTrend(BaseModel):
    metric_name: str
    current_value: float
    rolling_avg: float
    min_value: float
    max_value: float
    trend_direction: str  # STABLE, INCREASING, DECREASING
    is_anomalous: bool
    explanation: Optional[str] = None

class SpacecraftHealthOverview(BaseModel):
    overall_status: str  # NOMINAL, DEGRADED, CRITICAL
    overall_health_pct: float
    subsystems: List[SubsystemHealth]
    key_metrics: List[SubsystemTrend]
    rule_explanations: List[str]
