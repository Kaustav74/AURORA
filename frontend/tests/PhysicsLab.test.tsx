import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PhysicsLabContainer } from '../src/components/views/physics_lab/PhysicsLabContainer';
import App from '../src/App';
import { AuroraProvider } from '../src/context/AuroraContext';

const mockModels = [
  {
    model_id: 'MODEL-A-NEWTONIAN',
    model_name: 'Newtonian Point-Mass Baseline',
    model_version: '1.0.0',
    status: 'OPERATIONAL',
    category: 'CLASSICAL_BASELINE',
    provenance: {
      source_document: 'Lost Pages of the Lost Notebook of Ramanujan (Nath, 2024)',
      source_pages: 'Section 1.1',
      mathematical_definition: 'a = -GM r / |r|^3',
      physical_interpretation: 'Inverse-square central gravitational force.',
      implementation_notes: 'Vectorized 3D ODE formulation.',
      assumptions: ['Point-mass central body', 'Negligible test-mass gravity'],
      domain_of_validity: 'Weak gravity, r >> Rs',
    },
    parameters: { G: 6.6743e-11 },
    has_analytical_derivative: true,
    has_horizon_indicator: false,
  },
  {
    model_id: 'MODEL-B-RAMANUJAN-PSERIES-OPENING',
    model_name: 'Normalized Ramanujan p-Series Kernel',
    model_version: '1.0.0',
    status: 'OPERATIONAL',
    category: 'RAMANUJAN_DEFORMATION',
    provenance: {
      source_document: 'Lost Pages of the Lost Notebook of Ramanujan (Nath, 2024)',
      source_pages: 'Pages 1-14',
      mathematical_definition: 'Phi(R) = -GM K_hat(R) / R',
      physical_interpretation: 'Ramanujan p-series deformation of Newtonian potential.',
      implementation_notes: 'Quotient-rule analytical derivatives.',
      assumptions: ['Radial symmetry', 'Decoupled angular variables'],
      domain_of_validity: 'r > 0',
    },
    parameters: { R0: 1.0e6, r: 0.5, s: 2.0, Rref: 1.496e11 },
    has_analytical_derivative: true,
    has_horizon_indicator: true,
  },
];

const mockValidationSummary = {
  status: 'OPERATIONAL',
  timestamp: new Date().toISOString(),
  verified_models_count: 5,
  experimental_models_count: 2,
  blocked_models_count: 0,
  benchmarks: [
    {
      model_id: 'MODEL-A-NEWTONIAN',
      model_name: 'Newtonian Point-Mass Baseline',
      status: 'VERIFIED',
      analytical_energy_conservation: 'PASS (< 1.0e-5 rel)',
      finite_difference_cross_check: 'PASS (< 1.0e-6 rel)',
      schwarzschild_limit_test: 'N/A (Classical)',
      unphysical_orbit_handling: 'PASS (Singularity clamped)',
    },
  ],
};

// Global fetch mock
global.fetch = vi.fn().mockImplementation((url: string) => {
  if (url.includes('/api/v1/physics-lab/models')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockModels),
    });
  }
  if (url.includes('/api/v1/physics-lab/validation/summary')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockValidationSummary),
    });
  }
  if (url.includes('/api/v1/physics-lab/experiments')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve([]),
    });
  }
  if (url.includes('/api/v1/telemetry/current')) {
    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          run_id: 'RUN-TEST',
          timestamp_sim: 1.0,
          timestamp_wall: new Date().toISOString(),
          mode: 'NOMINAL',
          temperature_c: 20.0,
          battery_soc_pct: 100.0,
          bus_voltage_v: 28.0,
          current_draw_a: 2.0,
          comm_status: 'NOMINAL',
          signal_quality_pct: 100.0,
          attitude_error_deg: 0.0,
          angular_rate_deg_s: 0.0,
          storage_used_pct: 10.0,
          sensors_valid: true,
        }),
    });
  }
  if (url.includes('/api/v1/simulation/status')) {
    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          run_id: 'RUN-TEST',
          name: 'Test Run',
          status: 'RUNNING',
          seed: 42,
          cadence_hz: 1.0,
          sim_time_seconds: 1.0,
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

describe('AURORA Physics Lab Module', () => {
  it('renders research module banner and model metadata', async () => {
    render(<PhysicsLabContainer />);

    expect(screen.getByText('AURORA Physics Lab')).toBeInTheDocument();
    expect(screen.getByText('RESEARCH MODULE')).toBeInTheDocument();
    expect(
      screen.getByText(/LOST NOTEBOOK OF RAMANUJAN GRAVITATION SUITE/i)
    ).toBeInTheDocument();
  });

  it('switches between physics sub-tabs (models, validation, propulsion)', async () => {
    render(<PhysicsLabContainer />);

    // Click on Equation Registry tab
    const modelsTabBtn = screen.getByText('Equation Registry');
    fireEvent.click(modelsTabBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/REGISTERED THEORETICAL FORMULATIONS/i)
      ).toBeInTheDocument();
    });

    // Click on Validation Center tab
    const valTabBtn = screen.getByText('Validation Center');
    fireEvent.click(valTabBtn);

    await waitFor(() => {
      expect(
        screen.getByText('AUTOMATED SCIENTIFIC BENCHMARK MATRIX')
      ).toBeInTheDocument();
    });
  });

  it('navigates to Physics Lab from main AURORA navigation bar', async () => {
    render(
      <AuroraProvider>
        <App />
      </AuroraProvider>
    );

    // Look for Physics Lab navigation item in global nav
    const physicsNavBtn = screen.getByText('Physics Lab');
    expect(physicsNavBtn).toBeInTheDocument();

    fireEvent.click(physicsNavBtn);

    await waitFor(() => {
      expect(screen.getByText('AURORA Physics Lab')).toBeInTheDocument();
    });
  });
});
