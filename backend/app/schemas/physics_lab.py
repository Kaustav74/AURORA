"""
Pydantic Schemas for AURORA Physics Lab API
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ParameterSpec(BaseModel):
    symbol: str
    name: str
    si_unit: str
    default_value: Any
    is_tunable: bool


class PhysicsModelMetaResponse(BaseModel):
    model_id: str
    model_version: str
    display_name: str
    formulation_family: str
    source_document: str
    source_page_range: str
    source_equation_raw: str
    implementation_equation_latex: str
    parameters: List[ParameterSpec]
    domain_of_validity: str
    implementation_status: str
    scientific_validation_status: str
    known_limitations: str


class CreateExperimentRequest(BaseModel):
    name: str = Field(default="Compact-Object Exploration", max_length=150)
    model_id: str = Field(default="MODEL-A-NEWTONIAN")
    central_mass_kg: float = Field(default=1.989e30, gt=0.0)
    initial_position_m: List[float] = Field(default=[1.496e11, 0.0, 0.0])
    initial_velocity_mps: List[float] = Field(default=[0.0, 29784.8, 0.0])
    duration_seconds: float = Field(default=86400.0, gt=0.0)
    dt_initial: float = Field(default=60.0, gt=0.0)
    integrator: str = Field(default="DORMAND_PRINCE")
    rtol: float = Field(default=1.0e-7, gt=0.0)
    atol: float = Field(default=1.0e-9, gt=0.0)
    model_parameters: Optional[Dict[str, Any]] = None
    # Optional spacecraft propulsion specs
    spacecraft_dry_mass_kg: float = Field(default=500.0, gt=0.0)
    propellant_mass_kg: float = Field(default=200.0, ge=0.0)
    thrust_n: float = Field(default=0.0, ge=0.0)
    isp_seconds: float = Field(default=300.0, gt=0.0)
    maneuvers: Optional[List[Dict[str, Any]]] = None
    decimate_points: int = Field(default=500, ge=50, le=2000)


class AnomalyFindingResponse(BaseModel):
    id: str
    experiment_id: str
    time_sim: float
    model_id: str
    category: str
    severity: str
    title: str
    explanation: str
    detection_rule: str
    observed_value: Optional[str] = None
    reference_value: Optional[str] = None
    residual: Optional[float] = None
    threshold: Optional[str] = None
    status: str
    recommended_action: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: Optional[str] = None


class UpdateAnomalyStatusRequest(BaseModel):
    status: str  # NEW, INVESTIGATING, REPRODUCED, EXPLAINED, RESOLVED, DISMISSED
    resolution_notes: Optional[str] = None


class ExperimentSummaryResponse(BaseModel):
    id: str
    name: str
    model_id: str
    model_version: str
    central_mass_kg: float
    status: str
    termination_reason: str
    integrator: str
    sim_duration_s: float
    closest_approach_m: Optional[float] = None
    farthest_distance_m: Optional[float] = None
    max_energy_drift: Optional[float] = None
    created_at: str


class ExperimentDetailResponse(ExperimentSummaryResponse):
    config: Dict[str, Any]
    summary: Dict[str, Any]
    events: List[Dict[str, Any]]
    anomalies: List[AnomalyFindingResponse]


class TrajectoryPoint(BaseModel):
    t_sim: float
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    radius_m: float
    speed_mps: float
    specific_energy: float
    energy_drift_rel: float
    angular_momentum_mag: float
    h_drift_rel: float
    total_mass_kg: float
    propellant_mass_kg: float
    grav_acceleration_mps2: float
    thrust_acceleration_mps2: float
    horizon_indicator_H: Optional[float] = None


class TrajectoryResponse(BaseModel):
    experiment_id: str
    model_id: str
    point_count: int
    points: List[TrajectoryPoint]


class CompareModelsRequest(BaseModel):
    name: str = Field(default="Gravitational Model Comparison")
    model_ids: List[str] = Field(default=["MODEL-A-NEWTONIAN", "MODEL-B-RAMANUJAN-PSERIES-OPENING"])
    central_mass_kg: float = Field(default=1.989e30, gt=0.0)
    initial_position_m: List[float] = Field(default=[1.0e7, 0.0, 0.0])
    initial_velocity_mps: List[float] = Field(default=[0.0, 3600.0, 0.0])
    duration_seconds: float = Field(default=18000.0, gt=0.0)
    integrator: str = Field(default="DORMAND_PRINCE")
    dt_initial: float = Field(default=10.0, gt=0.0)
    rtol: float = Field(default=1.0e-7, gt=0.0)
    atol: float = Field(default=1.0e-9, gt=0.0)
    common_model_parameters: Optional[Dict[str, Any]] = None


class ParameterSweepRequest(BaseModel):
    model_id: str
    param_name: str
    param_values: List[float]
    base_parameters: Optional[Dict[str, Any]] = None
    central_mass_kg: float = Field(default=1.989e30)
    initial_position_m: List[float] = Field(default=[1.0e7, 0.0, 0.0])
    initial_velocity_mps: List[float] = Field(default=[0.0, 3600.0, 0.0])
    duration_seconds: float = Field(default=7200.0)


class ParameterFitRequest(BaseModel):
    model_id: str
    param_to_fit: str
    initial_guess: float
    bounds: List[float]  # [min, max]
    target_radial_speeds: List[Dict[str, float]]  # [{"r": ..., "v_target": ...}]
    central_mass_kg: float = Field(default=1.989e30)
    base_parameters: Optional[Dict[str, Any]] = None
