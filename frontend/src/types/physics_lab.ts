export interface ProvenanceInfo {
  source_document: string;
  source_pages: string;
  mathematical_definition: string;
  physical_interpretation: string;
  implementation_notes: string;
  assumptions: string[];
  domain_of_validity: string;
}

export interface PhysicsModelMeta {
  model_id: string;
  model_version: string;
  display_name?: string;
  model_name?: string;
  formulation_family?: string;
  source_document?: string;
  source_page_range?: string;
  source_equation_raw?: string;
  implementation_equation_latex?: string;
  parameters?: any;
  conserved_quantities?: string[];
  domain_of_validity?: string;
  implementation_status?: string;
  scientific_validation_status?: string;
  known_limitations?: string;
  test_references?: string[];
  status?: string;
  category?: string;
  provenance?: ProvenanceInfo;
  has_analytical_derivative?: boolean;
  has_horizon_indicator?: boolean;
}

export interface TrajectoryPoint {
  t_sim_s: number;
  position: [number, number, number];
  velocity: [number, number, number];
  radius_m: number;
  speed_mps: number;
  energy_drift_rel: number;
  angular_momentum_drift_rel: number;
  spacecraft_mass_kg: number;
  propellant_mass_kg: number;
  thrust_accel_mps2: number;
}

export interface TrajectoryPayload {
  experiment_id: string;
  point_count: number;
  points: TrajectoryPoint[];
}

export interface PhysicsEvent {
  time_sim: number;
  event_type: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  description: string;
  position: [number, number, number];
  radius: number;
}

export interface PhysicsAnomaly {
  id: string;
  experiment_id: string;
  time_sim: number;
  model_id: string;
  category: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  title: string;
  explanation: string;
  detection_rule: string;
  observed_value?: string;
  reference_value?: string;
  residual?: number;
  threshold?: string;
  status: 'NEW' | 'INVESTIGATING' | 'REPRODUCED' | 'RESOLVED' | 'DISMISSED';
  recommended_action?: string;
  resolution_notes?: string;
  created_at?: string;
}

export interface PhysicsExperiment {
  id: string;
  name: string;
  model_id: string;
  model_version: string;
  central_mass_kg: number;
  status: string;
  termination_reason: string;
  integrator: string;
  sim_duration_s: number;
  closest_approach_m?: number;
  farthest_distance_m?: number;
  max_energy_drift?: number;
  created_at?: string;
  config?: any;
  summary?: any;
  events?: PhysicsEvent[];
  anomalies?: PhysicsAnomaly[];
}

export interface CreateExperimentPayload {
  name: string;
  model_id: string;
  central_mass_kg: number;
  initial_position_m: [number, number, number];
  initial_velocity_mps: [number, number, number];
  duration_seconds: number;
  dt_initial?: number;
  integrator?: string;
  model_parameters?: Record<string, any>;
  spacecraft_dry_mass_kg?: number;
  propellant_mass_kg?: number;
  thrust_n?: number;
  isp_seconds?: number;
  maneuvers?: Array<{
    type: 'CONTINUOUS' | 'IMPULSIVE';
    t_start: number;
    t_end?: number;
    delta_v_mps?: [number, number, number];
    direction_mode?: 'PROGRADE' | 'RETROGRADE' | 'RADIAL_OUT' | 'RADIAL_IN' | 'NORMAL' | 'FIXED_VECTOR';
    vector?: [number, number, number];
  }>;
  decimate_points?: number;
}

export interface CompareModelsPayload {
  name: string;
  model_ids: string[];
  central_mass_kg: number;
  initial_position_m: [number, number, number];
  initial_velocity_mps: [number, number, number];
  duration_seconds: number;
  dt_initial?: number;
  integrator?: string;
  decimate_points?: number;
}

export interface ParameterSweepPayload {
  model_id: string;
  parameter_name: string;
  values: number[];
  central_mass_kg?: number;
  initial_position_m?: [number, number, number];
  initial_velocity_mps?: [number, number, number];
  duration_seconds?: number;
}

export interface ParameterFitPayload {
  model_id: string;
  parameter_name: string;
  bounds: [number, number];
  observations: Array<{
    t: number;
    r: number;
    vr?: number;
    v_mag?: number;
  }>;
  central_mass_kg?: number;
  initial_position_m?: [number, number, number];
  initial_velocity_mps?: [number, number, number];
}

export interface ValidationSummary {
  status: string;
  timestamp: string;
  verified_models_count: number;
  experimental_models_count: number;
  blocked_models_count: number;
  benchmarks: Array<{
    model_id: string;
    model_name: string;
    status: string;
    analytical_energy_conservation: string;
    finite_difference_cross_check: string;
    schwarzschild_limit_test: string;
    unphysical_orbit_handling: string;
  }>;
}
