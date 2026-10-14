import {
  TelemetryFrame,
  SimulationStatusResponse,
  SpacecraftStateResponse,
  CommandItem,
  IncidentItem,
  EventItem,
  MissionTaskItem,
  ScheduleResponse,
  ScenarioItem,
  ScenarioRunItem,
  HealthOverview,
  RequirementItem,
  VerificationCaseItem,
  RiskItem,
  DecisionItem,
  InterfaceItem,
  IssueItem,
  ReadinessSummary,
  MissionReportSummary,
  ReplayFramesResponse,
} from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = `HTTP Error ${response.status} (${response.statusText})`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Health & Metadata
  getHealth: () => fetchJson<{ status: string; version: string; disclaimer: string }>('/health'),
  getMetadata: () => fetchJson<Record<string, any>>('/v1/metadata'),

  // Simulation
  getSimulationStatus: () => fetchJson<SimulationStatusResponse>('/v1/simulation/status'),
  startSimulation: (name: string, seed: number = 42, cadence_hz: number = 1.0) =>
    fetchJson<SimulationStatusResponse>('/v1/simulation/start', {
      method: 'POST',
      body: JSON.stringify({ name, seed, cadence_hz }),
    }),
  pauseSimulation: () => fetchJson<SimulationStatusResponse>('/v1/simulation/pause', { method: 'POST' }),
  resumeSimulation: () => fetchJson<SimulationStatusResponse>('/v1/simulation/resume', { method: 'POST' }),
  stopSimulation: () => fetchJson<SimulationStatusResponse>('/v1/simulation/stop', { method: 'POST' }),
  stepSimulation: (dt: number = 1.0) => fetchJson<any>(`/v1/simulation/step?dt=${dt}`, { method: 'POST' }),
  injectFault: (fault_type: string, intensity: number = 1.0, target_value?: number) =>
    fetchJson<any>('/v1/faults/inject', {
      method: 'POST',
      body: JSON.stringify({ fault_type, intensity, target_value }),
    }),

  // Telemetry
  getCurrentTelemetry: () => fetchJson<TelemetryFrame>('/v1/telemetry/current'),
  getTelemetryHistory: (limit: number = 100, run_id?: string) =>
    fetchJson<TelemetryFrame[]>(`/v1/telemetry/history?limit=${limit}${run_id ? `&run_id=${run_id}` : ''}`),

  // Spacecraft State
  getCurrentState: () => fetchJson<SpacecraftStateResponse>('/v1/state/current'),
  getStateHistory: (run_id?: string) =>
    fetchJson<SpacecraftStateResponse[]>(`/v1/state/history${run_id ? `?run_id=${run_id}` : ''}`),
  requestRecovery: (requested_by: string, reason: string) =>
    fetchJson<any>('/v1/state/recovery-request', {
      method: 'POST',
      body: JSON.stringify({ requested_by, reason }),
    }),

  // Commands
  getCommands: (run_id?: string) =>
    fetchJson<CommandItem[]>(`/v1/commands${run_id ? `?run_id=${run_id}` : ''}`),
  submitCommand: (command_type: string, parameters: Record<string, any>, issued_by: string = 'OPERATOR', idempotency_key?: string) =>
    fetchJson<CommandItem>('/v1/commands', {
      method: 'POST',
      body: JSON.stringify({ command_type, parameters, issued_by, idempotency_key }),
    }),

  // Incidents
  getIncidents: (run_id?: string) =>
    fetchJson<IncidentItem[]>(`/v1/incidents${run_id ? `?run_id=${run_id}` : ''}`),
  acknowledgeIncident: (id: string, acknowledged_by: string = 'OPERATOR') =>
    fetchJson<IncidentItem>(`/v1/incidents/${id}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ acknowledged_by }),
    }),
  resolveIncident: (id: string, reason: string, resolved_by: string = 'OPERATOR') =>
    fetchJson<IncidentItem>(`/v1/incidents/${id}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ reason, resolved_by }),
    }),

  // Events & Replay
  getEvents: (run_id?: string, limit: number = 100) =>
    fetchJson<EventItem[]>(`/v1/events?limit=${limit}${run_id ? `&run_id=${run_id}` : ''}`),
  getReplayTimeline: (run_id: string) => fetchJson<any>(`/v1/events/replay/${run_id}`),
  getReplayFrames: (run_id: string) => fetchJson<ReplayFramesResponse>(`/v1/events/replay/${run_id}/frames`),

  // Mission Planning
  getTasks: () => fetchJson<MissionTaskItem[]>('/v1/tasks'),
  createTask: (task: Partial<MissionTaskItem>) =>
    fetchJson<MissionTaskItem>('/v1/tasks', { method: 'POST', body: JSON.stringify(task) }),
  updateTask: (id: string, task: Partial<MissionTaskItem>) =>
    fetchJson<MissionTaskItem>(`/v1/tasks/${id}`, { method: 'PUT', body: JSON.stringify(task) }),
  deleteTask: (id: string) => fetchJson<any>(`/v1/tasks/${id}`, { method: 'DELETE' }),
  generateSchedule: () => fetchJson<ScheduleResponse>('/v1/schedules/generate', { method: 'POST' }),

  // Scenarios
  getScenarios: () => fetchJson<ScenarioItem[]>('/v1/scenarios'),
  runScenario: (id: string) => fetchJson<ScenarioRunItem>(`/v1/scenarios/${id}/run`, { method: 'POST' }),
  getScenarioRuns: () => fetchJson<ScenarioRunItem[]>('/v1/scenario-runs'),

  // Health Intelligence
  getHealthOverview: (run_id?: string) =>
    fetchJson<HealthOverview>(`/v1/health-intel/overview${run_id ? `?run_id=${run_id}` : ''}`),

  // Systems Engineering
  getRequirements: () => fetchJson<RequirementItem[]>('/v1/systems-engineering/requirements'),
  getVerificationCases: () => fetchJson<VerificationCaseItem[]>('/v1/systems-engineering/verification-cases'),
  executeVerificationCase: (id: string, status: string, evidence_summary: string) =>
    fetchJson<VerificationCaseItem>(`/v1/systems-engineering/verification-cases/${id}/execute`, {
      method: 'POST',
      body: JSON.stringify({ status, evidence_summary }),
    }),
  getRisks: () => fetchJson<RiskItem[]>('/v1/systems-engineering/risks'),
  getDecisions: () => fetchJson<DecisionItem[]>('/v1/systems-engineering/decisions'),
  getInterfaces: () => fetchJson<InterfaceItem[]>('/v1/systems-engineering/interfaces'),
  getIssues: () => fetchJson<IssueItem[]>('/v1/systems-engineering/issues'),
  getReadinessSummary: () => fetchJson<ReadinessSummary>('/v1/systems-engineering/readiness'),

  // Reports
  getMissionSummary: () => fetchJson<MissionReportSummary>('/v1/reports/mission-summary'),
};
