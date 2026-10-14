export type SpacecraftMode =
  | 'STANDBY'
  | 'NOMINAL'
  | 'DEGRADED'
  | 'SAFE_MODE'
  | 'RECOVERY'
  | 'SIMULATION_STOPPED';

export type SimulationStatus = 'STOPPED' | 'RUNNING' | 'PAUSED';

export type CommStatus = 'NOMINAL' | 'DEGRADED' | 'LOST';

export interface TelemetryFrame {
  id?: number;
  run_id: string;
  timestamp_sim: number;
  timestamp_wall: string;
  mode: SpacecraftMode;
  temperature_c: number;
  battery_soc_pct: number;
  bus_voltage_v: number;
  current_draw_a: number;
  comm_status: CommStatus;
  signal_quality_pct: number;
  attitude_error_deg: number;
  angular_rate_deg_s: number;
  storage_used_pct: number;
  sensors_valid: boolean;
  metadata?: Record<string, any>;
  is_stale?: boolean;
}

export interface SimulationStatusResponse {
  run_id: string | null;
  name: string | null;
  status: SimulationStatus;
  seed: number;
  cadence_hz: number;
  sim_time_seconds: number;
  start_wall_time: string | null;
  is_active: boolean;
}

export interface SpacecraftStateResponse {
  id?: number;
  run_id: string;
  mode: SpacecraftMode;
  previous_mode?: SpacecraftMode;
  reason: string;
  source: string;
  timestamp_sim: number;
  timestamp_wall: string;
}

export interface CommandItem {
  id: string;
  run_id?: string;
  idempotency_key?: string;
  command_type: string;
  parameters: Record<string, any>;
  issued_by: string;
  status: 'PENDING' | 'VALIDATED' | 'REJECTED' | 'EXECUTING' | 'COMPLETED' | 'FAILED';
  rejection_reason?: string;
  result?: Record<string, any>;
  created_at: string;
  executed_at?: string;
}

export interface IncidentItem {
  id: string;
  run_id?: string;
  fault_type: string;
  severity: 'WARNING' | 'CRITICAL';
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'FALSE_POSITIVE';
  summary: string;
  details: string;
  first_seen_sim: number;
  last_seen_sim: number;
  acknowledged_at?: string;
  acknowledged_by?: string;
  resolved_at?: string;
  resolution_reason?: string;
  telemetry_snapshot?: Record<string, any>;
}

export interface EventItem {
  id: string;
  run_id?: string;
  event_type: string;
  category: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  message: string;
  details?: Record<string, any>;
  timestamp_sim: number;
  timestamp_wall: string;
}

export interface MissionTaskItem {
  id: string;
  title: string;
  description: string;
  priority: number;
  duration_minutes: number;
  earliest_start_minutes: number;
  deadline_minutes?: number;
  dependencies: string[];
  resources?: Record<string, any>;
  status: string;
  scheduled_start_minutes?: number;
  scheduled_end_minutes?: number;
  scheduling_notes?: string;
}

export interface ScheduleResponse {
  success: boolean;
  total_tasks: number;
  scheduled_tasks: number;
  unscheduled_tasks: number;
  conflicts: string[];
  makespan_minutes: number;
  tasks: MissionTaskItem[];
}

export interface ScenarioItem {
  id: string;
  name: string;
  description: string;
  seed: number;
  initial_config: Record<string, any>;
  fault_schedule: any[];
  expected_outcomes: Record<string, any>;
  version: string;
}

export interface ScenarioRunItem {
  id: string;
  scenario_id: string;
  run_id?: string;
  status: string;
  seed: number;
  observed_outcomes?: Record<string, any>;
  pass_fail?: string;
  deviations?: string[];
  started_at: string;
  completed_at?: string;
}

export interface SubsystemHealth {
  name: string;
  status: 'NOMINAL' | 'DEGRADED' | 'CRITICAL';
  score_pct: number;
  summary: string;
  active_warnings: string[];
}

export interface SubsystemTrend {
  metric_name: string;
  current_value: number;
  rolling_avg: number;
  min_value: number;
  max_value: number;
  trend_direction: 'STABLE' | 'INCREASING' | 'DECREASING';
  is_anomalous: boolean;
  explanation?: string;
}

export interface HealthOverview {
  overall_status: 'NOMINAL' | 'DEGRADED' | 'CRITICAL';
  overall_health_pct: number;
  subsystems: SubsystemHealth[];
  key_metrics: SubsystemTrend[];
  rule_explanations: string[];
}

export interface RequirementItem {
  id: string;
  title: string;
  statement: string;
  rationale: string;
  priority: string;
  category: string;
  verification_method: string;
  acceptance_criteria: string;
  status: string;
  linked_test_ids: string[];
  verification_status: 'NOT RUN' | 'PASS' | 'FAIL' | 'BLOCKED' | 'UNLINKED';
}

export interface VerificationCaseItem {
  id: string;
  title: string;
  purpose: string;
  preconditions: string;
  test_procedure: string;
  expected_result: string;
  linked_requirement_ids: string[];
  latest_status: 'NOT RUN' | 'PASS' | 'FAIL' | 'BLOCKED';
  executed_at?: string;
  evidence_summary?: string;
}

export interface ReadinessSummary {
  total_requirements: number;
  verified_requirements: number;
  unverified_requirements: number;
  unlinked_requirements: number;
  requirement_coverage_pct: number;
  total_verification_cases: number;
  cases_passed: number;
  cases_failed: number;
  cases_not_run: number;
  cases_blocked: number;
  open_risks_count: number;
  critical_risks_count: number;
  open_issues_count: number;
  readiness_assessment: string;
  disclaimer: string;
}

export interface RiskItem {
  id: string;
  description: string;
  likelihood: number;
  impact: number;
  score: number;
  mitigation: string;
  owner?: string;
  status: string;
  review_date?: string;
}

export interface DecisionItem {
  id: string;
  title: string;
  context: string;
  decision: string;
  alternatives: string;
  consequences: string;
  status: string;
  date: string;
}

export interface InterfaceItem {
  id: string;
  name: string;
  producer: string;
  consumer: string;
  contract_spec: string;
  version: string;
  limitations: string;
}

export interface IssueItem {
  id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  related_module: string;
  resolution_notes?: string;
}

export interface MissionReportSummary {
  generated_at: string;
  run_id?: string;
  simulation_time_seconds: number;
  spacecraft_mode: string;
  total_telemetry_frames: number;
  total_events: number;
  open_incidents: number;
  resolved_incidents: number;
  total_commands: number;
  readiness_score_pct: number;
  notes: string[];
  disclaimer: string;
}

export interface ReplayFrame {
  timestamp_sim: number;
  mode: SpacecraftMode;
  temperature_c: number;
  battery_soc_pct: number;
  bus_voltage_v: number;
  current_draw_a: number;
  comm_status: CommStatus;
  signal_quality_pct: number;
  attitude_error_deg: number;
  angular_rate_deg_s: number;
  storage_used_pct: number;
  sensors_valid: boolean;
}

export interface ReplayFramesResponse {
  run_id: string;
  min_sim_time: number;
  max_sim_time: number;
  total_frames: number;
  frames: ReplayFrame[];
  events_count: number;
}
