import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../src/App';
import { AuroraProvider } from '../src/context/AuroraContext';

// Mock fetch for tests
global.fetch = vi.fn().mockImplementation((url: string) => {
  if (url.includes('/api/v1/telemetry/current')) {
    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          run_id: 'TEST-RUN-01',
          timestamp_sim: 12.5,
          timestamp_wall: new Date().toISOString(),
          mode: 'NOMINAL',
          temperature_c: 24.2,
          battery_soc_pct: 95.0,
          bus_voltage_v: 28.1,
          current_draw_a: 3.4,
          comm_status: 'NOMINAL',
          signal_quality_pct: 98.0,
          attitude_error_deg: 0.12,
          angular_rate_deg_s: 0.01,
          storage_used_pct: 35.0,
          sensors_valid: true,
          metadata: {},
        }),
    });
  }
  if (url.includes('/api/v1/simulation/status')) {
    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          run_id: 'TEST-RUN-01',
          name: 'Unit Test Mission',
          status: 'RUNNING',
          seed: 42,
          cadence_hz: 1.0,
          sim_time_seconds: 12.5,
          start_wall_time: new Date().toISOString(),
          is_active: true,
        }),
    });
  }
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve([]),
  });
});

describe('Project AURORA Frontend Shell', () => {
  it('renders persistent brand identity and SIMULATION badge', async () => {
    render(
      <AuroraProvider>
        <App />
      </AuroraProvider>
    );

    // Verify brand
    expect(screen.getByText('AURORA')).toBeInTheDocument();

    // Verify persistent SIMULATION ONLY warning indicator
    expect(screen.getByText('SIMULATION ONLY')).toBeInTheDocument();

    // Verify primary navigation tabs render
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Telemetry')).toBeInTheDocument();
    expect(screen.getByText('Command Centre')).toBeInTheDocument();
    expect(screen.getByText('Faults & Incidents')).toBeInTheDocument();
    expect(screen.getByText('Scenario Lab')).toBeInTheDocument();
    expect(screen.getByText('Verification')).toBeInTheDocument();
  });
});
