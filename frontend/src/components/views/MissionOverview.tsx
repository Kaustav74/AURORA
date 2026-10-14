import React, { useState } from 'react';
import { useAurora } from '../../context/AuroraContext';
import { TelemetryCard } from '../common/TelemetryCard';
import {
  Play,
  Pause,
  Square,
  StepForward,
  ShieldAlert,
  AlertTriangle,
  Radio,
  CheckCircle,
  Thermometer,
  BatteryCharging,
  Zap,
  Compass,
  ArrowRight,
} from 'lucide-react';

interface MissionOverviewProps {
  onNavigateToTab: (tab: any) => void;
}

export const MissionOverview: React.FC<MissionOverviewProps> = ({ onNavigateToTab }) => {
  const {
    telemetry,
    telemetryHistory,
    simStatus,
    spacecraftState,
    incidents,
    events,
    isStale,
    startSim,
    pauseSim,
    resumeSim,
    stopSim,
    stepSim,
    recoverSpacecraft,
  } = useAurora();

  const [isRecovering, setIsRecovering] = useState(false);
  const [recoveryError, setRecoveryError] = useState<string | null>(null);

  const currentMode = spacecraftState?.mode || telemetry?.mode || 'STANDBY';
  const openIncidents = incidents.filter((i) => i.status === 'OPEN' || i.status === 'ACKNOWLEDGED');

  const handleRecovery = async () => {
    setIsRecovering(true);
    setRecoveryError(null);
    try {
      await recoverSpacecraft('Ground operator commanded post-cooling recovery verification.');
    } catch (err: any) {
      setRecoveryError(err.message || 'Recovery failed.');
    } finally {
      setIsRecovering(false);
    }
  };

  // Helper to render responsive SVG mini line charts
  const renderSvgLineChart = (
    data: number[],
    color: string,
    minVal: number,
    maxVal: number,
    thresholdVal?: number
  ) => {
    if (!data || data.length < 2) {
      return (
        <div className="h-28 flex items-center justify-center text-xs text-slate-500 font-mono">
          Accumulating time-series frames...
        </div>
      );
    }

    const width = 300;
    const height = 90;
    const padding = 10;
    const effectiveHeight = height - padding * 2;
    const effectiveWidth = width - padding * 2;

    const span = Math.max(0.1, maxVal - minVal);
    const points = data.map((val, idx) => {
      const x = padding + (idx / (data.length - 1)) * effectiveWidth;
      const normalizedY = (val - minVal) / span;
      const y = height - padding - normalizedY * effectiveHeight;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });

    let thresholdY: number | null = null;
    if (thresholdVal !== undefined && thresholdVal >= minVal && thresholdVal <= maxVal) {
      thresholdY = height - padding - ((thresholdVal - minVal) / span) * effectiveHeight;
    }

    return (
      <svg className="w-full h-28 overflow-visible" viewBox={`0 0 ${width} ${height}`}>
        {/* Threshold Reference Line */}
        {thresholdY !== null && (
          <g>
            <line
              x1={padding}
              y1={thresholdY}
              x2={width - padding}
              y2={thresholdY}
              stroke="#ff3344"
              strokeDasharray="4 3"
              strokeWidth="1.5"
            />
            <text x={width - padding - 65} y={thresholdY - 3} fill="#ff3344" fontSize="9" fontFamily="monospace">
              LIMIT: {thresholdVal}°C
            </text>
          </g>
        )}
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points.join(' ')}
        />
        {/* Latest Point Dot */}
        {points.length > 0 && (
          <circle
            cx={points[points.length - 1].split(',')[0]}
            cy={points[points.length - 1].split(',')[1]}
            r="3.5"
            fill={color}
          />
        )}
      </svg>
    );
  };

  const tempHistory = telemetryHistory.map((t) => t.temperature_c);
  const socHistory = telemetryHistory.map((t) => t.battery_soc_pct);
  const signalHistory = telemetryHistory.map((t) => t.signal_quality_pct);

  return (
    <div className="space-y-5">
      {/* SAFE_MODE Emergency Banner */}
      {currentMode === 'SAFE_MODE' && (
        <div className="p-4 rounded-xl border border-red-500/60 bg-red-950/40 glow-red">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-start space-x-3">
              <ShieldAlert className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5 animate-bounce" />
              <div>
                <h3 className="font-bold text-red-200 text-sm tracking-wide">
                  SPACECRAFT SAFE_MODE ACTIVATED
                </h3>
                <p className="text-xs text-red-300/90 font-mono mt-0.5">
                  {spacecraftState?.reason || 'Critical thermal or electrical threshold violated.'}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Non-essential loads shed. Direct return to NOMINAL is restricted. Verify all preconditions before recovery.
                </p>
              </div>
            </div>

            <div className="flex flex-col items-end gap-1.5">
              <button
                onClick={handleRecovery}
                disabled={isRecovering}
                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 active:bg-red-700 text-white font-mono text-xs font-semibold shadow-lg transition flex items-center gap-1.5 disabled:opacity-50"
              >
                {isRecovering ? 'VERIFYING PRECONDITIONS...' : 'EXECUTE RECOVERY PROCEDURE'}
              </button>
              {recoveryError && (
                <span className="text-[11px] font-mono text-red-300 max-w-md text-right">
                  {recoveryError}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Simulation Controls & Run Status Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-xs font-mono text-slate-400">ACTIVE SCENARIO RUN</div>
          <div className="text-base font-bold text-white flex items-center gap-2">
            <span>{simStatus?.name || 'Default Simulation'}</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-space-700 text-cyan-300">
              STATUS: {simStatus?.status || 'IDLE'}
            </span>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center space-x-2 font-mono text-xs">
          {simStatus?.status === 'RUNNING' ? (
            <button
              onClick={() => pauseSim()}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 transition"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>PAUSE</span>
            </button>
          ) : (
            <button
              onClick={() => (simStatus?.status === 'PAUSED' ? resumeSim() : startSim('Orbital Pass 1'))}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 transition"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{simStatus?.status === 'PAUSED' ? 'RESUME' : 'START RUN'}</span>
            </button>
          )}

          <button
            onClick={() => stopSim()}
            disabled={simStatus?.status === 'STOPPED'}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-space-700 hover:bg-space-600 text-slate-300 border border-space-500 transition disabled:opacity-40"
          >
            <Square className="w-3.5 h-3.5" />
            <span>STOP</span>
          </button>

          <button
            onClick={() => stepSim(1.0)}
            title="Step simulation clock forward by 1 second"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 transition"
          >
            <StepForward className="w-3.5 h-3.5" />
            <span>STEP +1s</span>
          </button>
        </div>
      </div>

      {/* Primary Telemetry Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <TelemetryCard
          label="CORE TEMP"
          value={telemetry ? telemetry.temperature_c.toFixed(1) : '--'}
          unit="°C"
          status={
            telemetry && telemetry.temperature_c >= 75.0
              ? 'CRITICAL'
              : telemetry && telemetry.temperature_c > 45.0
              ? 'CAUTION'
              : 'NOMINAL'
          }
          threshold="SAFE: <75°C"
          subtext="Avionics thermal loop"
        />

        <TelemetryCard
          label="BATTERY SOC"
          value={telemetry ? telemetry.battery_soc_pct.toFixed(1) : '--'}
          unit="%"
          status={
            telemetry && telemetry.battery_soc_pct < 20.0
              ? 'CRITICAL'
              : telemetry && telemetry.battery_soc_pct < 40.0
              ? 'CAUTION'
              : 'NOMINAL'
          }
          threshold="MIN: 20%"
          subtext="Secondary Li-Ion"
        />

        <TelemetryCard
          label="BUS VOLTAGE"
          value={telemetry ? telemetry.bus_voltage_v.toFixed(2) : '--'}
          unit="V"
          status={telemetry && telemetry.bus_voltage_v < 22.0 ? 'CRITICAL' : 'NOMINAL'}
          threshold="NOM: 28.0V"
          subtext="Unregulated bus"
        />

        <TelemetryCard
          label="CURRENT DRAW"
          value={telemetry ? telemetry.current_draw_a.toFixed(2) : '--'}
          unit="A"
          status={currentMode === 'SAFE_MODE' ? 'CAUTION' : 'NOMINAL'}
          subtext={currentMode === 'SAFE_MODE' ? 'Load shed active' : 'All loads active'}
        />

        <TelemetryCard
          label="COMM LINK"
          value={telemetry ? telemetry.comm_status : '--'}
          status={
            telemetry?.comm_status === 'LOST'
              ? 'CRITICAL'
              : telemetry?.comm_status === 'DEGRADED'
              ? 'CAUTION'
              : 'NOMINAL'
          }
          subtext={telemetry ? `Signal: ${telemetry.signal_quality_pct.toFixed(0)}%` : '--'}
        />

        <TelemetryCard
          label="ADCS ERROR"
          value={telemetry ? telemetry.attitude_error_deg.toFixed(2) : '--'}
          unit="°"
          status={telemetry && telemetry.attitude_error_deg > 15.0 ? 'CRITICAL' : 'NOMINAL'}
          threshold="BUDGET: 1.0°"
          subtext="Body pointing offset"
        />
      </div>

      {/* Live Engineering Trend Charts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Thermal Chart */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-1.5 text-xs font-mono text-slate-300">
              <Thermometer className="w-3.5 h-3.5 text-red-400" />
              <span>TEMPERATURE (°C)</span>
            </div>
            <span className="text-xs font-mono text-red-400">
              {telemetry ? `${telemetry.temperature_c.toFixed(1)}°C` : '--'}
            </span>
          </div>
          {renderSvgLineChart(tempHistory, '#ff3344', 10, 90, 75.0)}
          <div className="text-[10px] font-mono text-slate-500 mt-1 flex justify-between">
            <span>Fictional Safe Hold Limit: 75.0°C</span>
            <span>Historical Ticks: {tempHistory.length}</span>
          </div>
        </div>

        {/* Battery SOC Chart */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-1.5 text-xs font-mono text-slate-300">
              <BatteryCharging className="w-3.5 h-3.5 text-emerald-400" />
              <span>BATTERY SOC (%)</span>
            </div>
            <span className="text-xs font-mono text-emerald-400">
              {telemetry ? `${telemetry.battery_soc_pct.toFixed(1)}%` : '--'}
            </span>
          </div>
          {renderSvgLineChart(socHistory, '#00ff88', 0, 100, 20.0)}
          <div className="text-[10px] font-mono text-slate-500 mt-1 flex justify-between">
            <span>Critical Cutoff: 20.0%</span>
            <span>Bus Voltage: {telemetry ? `${telemetry.bus_voltage_v.toFixed(1)}V` : '--'}</span>
          </div>
        </div>

        {/* RF Signal Chart */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-1.5 text-xs font-mono text-slate-300">
              <Radio className="w-3.5 h-3.5 text-cyan-400" />
              <span>SIGNAL QUALITY (%)</span>
            </div>
            <span className="text-xs font-mono text-cyan-400">
              {telemetry ? `${telemetry.signal_quality_pct.toFixed(1)}%` : '--'}
            </span>
          </div>
          {renderSvgLineChart(signalHistory, '#00f0ff', 0, 100)}
          <div className="text-[10px] font-mono text-slate-500 mt-1 flex justify-between">
            <span>Link State: {telemetry?.comm_status || 'NOMINAL'}</span>
            <span>Bit Error Rate: nominal</span>
          </div>
        </div>
      </div>

      {/* Dual Split: Active Incidents & Real-time Event Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Active Incidents */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4">
          <div className="flex items-center justify-between pb-3 border-b border-space-700">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <h4 className="text-xs font-mono font-bold text-slate-200">
                ACTIVE FAULTS & INCIDENTS ({openIncidents.length})
              </h4>
            </div>
            <button
              onClick={() => onNavigateToTab('incidents')}
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              <span>MANAGE</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="mt-3 space-y-2">
            {openIncidents.length === 0 ? (
              <div className="py-6 text-center text-xs font-mono text-slate-500">
                No active incidents reported. All subsystems within operational bounds.
              </div>
            ) : (
              openIncidents.slice(0, 4).map((inc) => (
                <div
                  key={inc.id}
                  className={`p-2.5 rounded-lg border font-mono text-xs flex items-center justify-between ${
                    inc.severity === 'CRITICAL'
                      ? 'border-red-500/40 bg-red-950/20 text-red-300'
                      : 'border-amber-500/30 bg-amber-950/20 text-amber-300'
                  }`}
                >
                  <div>
                    <div className="font-bold flex items-center gap-2">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-black/40">
                        {inc.severity}
                      </span>
                      <span>{inc.fault_type}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{inc.summary}</div>
                  </div>
                  <div className="text-[10px] text-slate-400">
                    T+{inc.first_seen_sim.toFixed(0)}s
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Real-time Event Feed */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4">
          <div className="flex items-center justify-between pb-3 border-b border-space-700">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-cyan-400" />
              <h4 className="text-xs font-mono font-bold text-slate-200">
                RECENT OPERATIONS LOG ({events.length})
              </h4>
            </div>
            <button
              onClick={() => onNavigateToTab('events')}
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              <span>FULL LOG</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="mt-3 space-y-1.5 max-h-56 overflow-y-auto pr-1">
            {events.length === 0 ? (
              <div className="py-6 text-center text-xs font-mono text-slate-500">
                No telemetry events logged yet.
              </div>
            ) : (
              events.slice(0, 6).map((evt) => (
                <div
                  key={evt.id}
                  className="p-2 rounded bg-space-750 border border-space-700/60 font-mono text-xs flex items-baseline justify-between gap-2"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                        evt.severity === 'CRITICAL'
                          ? 'bg-red-400'
                          : evt.severity === 'WARNING'
                          ? 'bg-amber-400'
                          : 'bg-cyan-400'
                      }`}
                    />
                    <span className="text-slate-300 truncate">{evt.message}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 flex-shrink-0">
                    T+{evt.timestamp_sim.toFixed(1)}s
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
