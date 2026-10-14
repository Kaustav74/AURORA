import React, { useState } from 'react';
import { TrajectoryPoint } from '../../../types/physics_lab';
import { Activity, Gauge, TrendingUp, Layers } from 'lucide-react';

interface TelemetryChartsProps {
  trajectory: TrajectoryPoint[];
  currentIndex: number;
  onScrubIndex?: (index: number) => void;
}

export const TelemetryCharts: React.FC<TelemetryChartsProps> = ({
  trajectory,
  currentIndex,
  onScrubIndex,
}) => {
  const [activeMetric, setActiveMetric] = useState<'energy' | 'momentum' | 'radius' | 'speed' | 'mass'>('energy');

  if (!trajectory || trajectory.length === 0) {
    return (
      <div className="bg-space-900 border border-space-700 rounded-lg p-6 text-center text-slate-400 font-mono text-xs">
        NO TRAJECTORY DATA LOADED FOR DIAGNOSTIC PLOTTING
      </div>
    );
  }

  // Extract series based on selected metric
  const getMetricData = () => {
    switch (activeMetric) {
      case 'energy':
        return {
          title: 'Specific Orbital Energy Drift (ΔE / E₀)',
          unit: 'rel',
          values: trajectory.map((p) => Math.abs(p.energy_drift_rel)),
          color: '#38bdf8',
          logScale: true,
          threshold: 1.0e-4,
        };
      case 'momentum':
        return {
          title: 'Specific Angular Momentum Drift (Δh / h₀)',
          unit: 'rel',
          values: trajectory.map((p) => Math.abs(p.angular_momentum_drift_rel)),
          color: '#c084fc',
          logScale: true,
          threshold: 1.0e-4,
        };
      case 'radius':
        return {
          title: 'Radial Distance from Central Mass r(t)',
          unit: 'km',
          values: trajectory.map((p) => p.radius_m / 1000),
          color: '#34d399',
          logScale: false,
        };
      case 'speed':
        return {
          title: 'Orbital Speed Magnitude v(t)',
          unit: 'km/s',
          values: trajectory.map((p) => p.speed_mps / 1000),
          color: '#fbbf24',
          logScale: false,
        };
      case 'mass':
        return {
          title: 'Total Spacecraft Mass m(t)',
          unit: 'kg',
          values: trajectory.map((p) => p.spacecraft_mass_kg),
          color: '#f87171',
          logScale: false,
        };
    }
  };

  const metric = getMetricData();
  const rawValues = metric.values;
  const tValues = trajectory.map((p) => p.t_sim_s);

  // SVG dimensions
  const svgWidth = 800;
  const svgHeight = 220;
  const padLeft = 70;
  const padRight = 30;
  const padTop = 25;
  const padBottom = 35;
  const plotW = svgWidth - padLeft - padRight;
  const plotH = svgHeight - padTop - padBottom;

  const tMin = tValues[0];
  const tMax = Math.max(tValues[tValues.length - 1], tMin + 1e-9);

  let yMin = Math.min(...rawValues);
  let yMax = Math.max(...rawValues);
  if (metric.logScale) {
    yMin = Math.max(1.0e-16, yMin);
    yMax = Math.max(1.0e-15, yMax);
  } else if (yMin === yMax) {
    yMin = yMin * 0.9;
    yMax = yMax * 1.1 + 1e-5;
  }

  const getX = (t: number) => padLeft + ((t - tMin) / (tMax - tMin)) * plotW;
  const getY = (val: number) => {
    if (metric.logScale) {
      const safeVal = Math.max(1.0e-16, val);
      const logMin = Math.log10(yMin);
      const logMax = Math.max(logMin + 1, Math.log10(yMax));
      const norm = (Math.log10(safeVal) - logMin) / (logMax - logMin);
      return padTop + plotH - norm * plotH;
    } else {
      const norm = (val - yMin) / (yMax - yMin);
      return padTop + plotH - norm * plotH;
    }
  };

  // Build SVG polyline points
  const pointsStr = trajectory
    .map((p, idx) => `${getX(p.t_sim_s).toFixed(1)},${getY(rawValues[idx]).toFixed(1)}`)
    .join(' ');

  // Current scrubber X position
  const currentT = trajectory[Math.min(currentIndex, trajectory.length - 1)]?.t_sim_s || 0;
  const scrubX = getX(currentT);

  return (
    <div className="bg-space-900 border border-space-700 rounded-lg p-4 space-y-4">
      {/* Metric Switcher Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-space-700/80 pb-3">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
          <Activity className="w-4 h-4 text-cyan-400" />
          <span className="font-bold">CONSERVATION INVARIANTS & TELEMETRY</span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setActiveMetric('energy')}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
              activeMetric === 'energy'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-800'
            }`}
          >
            Energy Drift (ΔE/E)
          </button>
          <button
            onClick={() => setActiveMetric('momentum')}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
              activeMetric === 'momentum'
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-800'
            }`}
          >
            Ang. Momentum (Δh/h)
          </button>
          <button
            onClick={() => setActiveMetric('radius')}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
              activeMetric === 'radius'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-800'
            }`}
          >
            Radius r(t)
          </button>
          <button
            onClick={() => setActiveMetric('speed')}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
              activeMetric === 'speed'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-800'
            }`}
          >
            Speed v(t)
          </button>
          <button
            onClick={() => setActiveMetric('mass')}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
              activeMetric === 'mass'
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-800'
            }`}
          >
            Mass m(t)
          </button>
        </div>
      </div>

      {/* SVG Diagnostic Chart */}
      <div className="relative w-full overflow-hidden bg-space-950 rounded-md border border-space-800 p-2">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-56 select-none"
          onClick={(e) => {
            if (!onScrubIndex) return;
            const rect = e.currentTarget.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const normX = Math.max(0, Math.min(1, (clickX - (padLeft * rect.width) / svgWidth) / ((plotW * rect.width) / svgWidth)));
            const targetIdx = Math.round(normX * (trajectory.length - 1));
            onScrubIndex(targetIdx);
          }}
        >
          {/* Grid lines */}
          <line
            x1={padLeft}
            y1={padTop + plotH}
            x2={padLeft + plotW}
            y2={padTop + plotH}
            stroke="#1e293b"
            strokeWidth="1"
          />
          <line
            x1={padLeft}
            y1={padTop + plotH / 2}
            x2={padLeft + plotW}
            y2={padTop + plotH / 2}
            stroke="#1e293b"
            strokeDasharray="3 3"
            strokeWidth="1"
          />
          <line
            x1={padLeft}
            y1={padTop}
            x2={padLeft + plotW}
            y2={padTop}
            stroke="#1e293b"
            strokeDasharray="3 3"
            strokeWidth="1"
          />

          {/* Tolerance Threshold Line if applicable */}
          {metric.threshold && (
            <line
              x1={padLeft}
              y1={getY(metric.threshold)}
              x2={padLeft + plotW}
              y2={getY(metric.threshold)}
              stroke="#ef4444"
              strokeDasharray="4 4"
              strokeWidth="1.2"
            />
          )}

          {/* Y Axis Labels */}
          <text
            x={padLeft - 8}
            y={padTop + 4}
            fill="#64748b"
            fontSize="10"
            fontFamily="monospace"
            textAnchor="end"
          >
            {metric.logScale ? `10^${Math.round(Math.log10(yMax))}` : yMax.toFixed(1)}
          </text>
          <text
            x={padLeft - 8}
            y={padTop + plotH / 2 + 4}
            fill="#64748b"
            fontSize="10"
            fontFamily="monospace"
            textAnchor="end"
          >
            {metric.logScale
              ? `10^${Math.round((Math.log10(yMin) + Math.log10(yMax)) / 2)}`
              : ((yMin + yMax) / 2).toFixed(1)}
          </text>
          <text
            x={padLeft - 8}
            y={padTop + plotH + 2}
            fill="#64748b"
            fontSize="10"
            fontFamily="monospace"
            textAnchor="end"
          >
            {metric.logScale ? `10^${Math.round(Math.log10(yMin))}` : yMin.toFixed(1)}
          </text>

          {/* X Axis Labels */}
          <text
            x={padLeft}
            y={svgHeight - 10}
            fill="#64748b"
            fontSize="10"
            fontFamily="monospace"
            textAnchor="start"
          >
            t = {tMin.toFixed(1)} s
          </text>
          <text
            x={padLeft + plotW}
            y={svgHeight - 10}
            fill="#64748b"
            fontSize="10"
            fontFamily="monospace"
            textAnchor="end"
          >
            t = {tMax.toFixed(1)} s
          </text>

          {/* Telemetry Plot Curve */}
          <polyline
            fill="none"
            stroke={metric.color}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={pointsStr}
          />

          {/* Active Scrubber Line */}
          <line
            x1={scrubX}
            y1={padTop}
            x2={scrubX}
            y2={padTop + plotH}
            stroke="#f59e0b"
            strokeWidth="1.5"
          />
          <circle
            cx={scrubX}
            cy={getY(rawValues[Math.min(currentIndex, rawValues.length - 1)])}
            r="4.5"
            fill="#f59e0b"
            stroke="#ffffff"
            strokeWidth="1.5"
          />
        </svg>

        {/* Current Metric Readout Pill */}
        <div className="flex items-center justify-between text-xs font-mono px-2 py-1 text-slate-400">
          <span>{metric.title}</span>
          <span className="text-amber-400 font-bold">
            Value @ t={currentT.toFixed(2)}s:{' '}
            {metric.logScale
              ? rawValues[Math.min(currentIndex, rawValues.length - 1)].toExponential(3)
              : rawValues[Math.min(currentIndex, rawValues.length - 1)].toFixed(3)}{' '}
            {metric.unit}
          </span>
        </div>
      </div>
    </div>
  );
};
