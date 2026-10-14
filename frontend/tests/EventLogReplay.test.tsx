import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EventLogView } from '../src/components/views/EventLogView';
import { AuroraProvider } from '../src/context/AuroraContext';

// Mock fetch for tests
global.fetch = vi.fn().mockImplementation((url: string) => {
  if (url.includes('/api/v1/simulation/status')) {
    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          run_id: 'RUN-TEST-REPLAY',
          name: 'Replay Test Run',
          status: 'RUNNING',
          seed: 42,
          cadence_hz: 1.0,
          sim_time_seconds: 30.0,
          start_wall_time: new Date().toISOString(),
          is_active: true,
        }),
    });
  }
  if (url.includes('/api/v1/events/replay/RUN-TEST-REPLAY/frames')) {
    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          run_id: 'RUN-TEST-REPLAY',
          min_sim_time: 0.0,
          max_sim_time: 20.0,
          total_frames: 3,
          frames: [
            {
              timestamp_sim: 0.0,
              mode: 'NOMINAL',
              temperature_c: 25.0,
              battery_soc_pct: 99.0,
              bus_voltage_v: 28.0,
              current_draw_a: 3.0,
              comm_status: 'NOMINAL',
              signal_quality_pct: 98.0,
              attitude_error_deg: 0.1,
              angular_rate_deg_s: 0.01,
              storage_used_pct: 10.0,
              sensors_valid: true,
            },
            {
              timestamp_sim: 10.0,
              mode: 'NOMINAL',
              temperature_c: 74.5,
              battery_soc_pct: 95.0,
              bus_voltage_v: 27.9,
              current_draw_a: 5.5,
              comm_status: 'NOMINAL',
              signal_quality_pct: 95.0,
              attitude_error_deg: 0.2,
              angular_rate_deg_s: 0.02,
              storage_used_pct: 12.0,
              sensors_valid: true,
            },
            {
              timestamp_sim: 20.0,
              mode: 'SAFE_MODE',
              temperature_c: 76.2,
              battery_soc_pct: 92.0,
              bus_voltage_v: 27.8,
              current_draw_a: 1.8,
              comm_status: 'NOMINAL',
              signal_quality_pct: 90.0,
              attitude_error_deg: 0.4,
              angular_rate_deg_s: 0.01,
              storage_used_pct: 13.0,
              sensors_valid: true,
            },
          ],
          events_count: 2,
        }),
    });
  }
  if (url.includes('/api/v1/events')) {
    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve([
          {
            id: 'EVT-001',
            run_id: 'RUN-TEST-REPLAY',
            event_type: 'SIMULATION_STARTED',
            category: 'OPERATIONS',
            severity: 'INFO',
            message: 'Simulation mission started.',
            timestamp_sim: 0.0,
            timestamp_wall: new Date().toISOString(),
          },
        ]),
    });
  }
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve([]),
  });
});

describe('Mission Event Log & Replay Scrubber', () => {
  it('renders event audit log and opens interactive historical replay scrubber', async () => {
    render(
      <AuroraProvider>
        <EventLogView />
      </AuroraProvider>
    );

    // Initial render checks
    expect(screen.getByText('MISSION EVENT LOG & REPLAY')).toBeInTheDocument();
    expect(screen.getByText('EXPORT CSV')).toBeInTheDocument();

    const openButton = screen.getByText('OPEN MISSION REPLAY SCRUBBER');
    expect(openButton).toBeInTheDocument();

    // Wait for provider to load initial simulation status and enable the button
    await waitFor(() => {
      expect(openButton.closest('button')).not.toBeDisabled();
    });

    // Trigger scrubber deck open
    fireEvent.click(openButton);

    // Wait for replay scrubber deck to open
    await waitFor(() => {
      expect(
        screen.getByText('HISTORICAL MISSION REPLAY MODE — READ ONLY (DOES NOT MUTATE LIVE SIMULATOR)')
      ).toBeInTheDocument();
    });

    // Check scrubber frame counters and controls
    expect(screen.getByText('PLAY')).toBeInTheDocument();
    expect(screen.getByText(/RECONSTRUCTED TELEMETRY SNAPSHOT/)).toBeInTheDocument();
    expect(screen.getByText('25.0°C')).toBeInTheDocument();

    // Step forward 1 frame
    const stepForwardBtn = screen.getByTitle('Step Forward (1 frame)');
    fireEvent.click(stepForwardBtn);

    // Now second frame at 74.5°C should be displayed
    await waitFor(() => {
      expect(screen.getByText('74.5°C')).toBeInTheDocument();
    });

    // Step forward again to 3rd frame (Safe Mode)
    fireEvent.click(stepForwardBtn);
    await waitFor(() => {
      expect(screen.getByText('76.2°C')).toBeInTheDocument();
      expect(screen.getByText('SAFE_MODE')).toBeInTheDocument();
    });
  });
});
