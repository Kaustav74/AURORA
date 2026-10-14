import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { TelemetryCard } from '../src/components/common/TelemetryCard';

describe('Telemetry Card Component', () => {
  it('renders metric label, value, unit, and threshold', () => {
    render(
      <TelemetryCard
        label="CORE TEMP"
        value={24.5}
        unit="°C"
        status="NOMINAL"
        threshold="SAFE: <75°C"
        subtext="Avionics thermal loop"
      />
    );

    expect(screen.getByText('CORE TEMP')).toBeInTheDocument();
    expect(screen.getByText('24.5')).toBeInTheDocument();
    expect(screen.getByText('°C')).toBeInTheDocument();
    expect(screen.getByText('SAFE: <75°C')).toBeInTheDocument();
    expect(screen.getByText('Avionics thermal loop')).toBeInTheDocument();
  });

  it('renders critical styling when status is CRITICAL', () => {
    const { container } = render(
      <TelemetryCard
        label="CORE TEMP"
        value={78.2}
        unit="°C"
        status="CRITICAL"
      />
    );

    expect(container.firstChild).toHaveClass('border-red-500/50');
  });
});
