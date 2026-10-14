import React from 'react';
import { useAurora } from '../../context/AuroraContext';
import { Activity, Radio, AlertTriangle, ShieldAlert, Cpu, RefreshCw } from 'lucide-react';

export const Header: React.FC = () => {
  const {
    connectionStatus,
    telemetry,
    simStatus,
    spacecraftState,
    isStale,
    lastUpdated,
    refreshAll,
  } = useAurora();

  const currentMode = spacecraftState?.mode || telemetry?.mode || 'STANDBY';

  const getModeBadgeClass = (mode: string) => {
    switch (mode) {
      case 'NOMINAL':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
      case 'SAFE_MODE':
        return 'bg-red-500/20 text-red-400 border-red-500/50 glow-red animate-pulse';
      case 'DEGRADED':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'RECOVERY':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/40';
      default:
        return 'bg-slate-700/40 text-slate-400 border-slate-600/40';
    }
  };

  const getConnectionDotClass = () => {
    switch (connectionStatus) {
      case 'CONNECTED':
        return 'bg-emerald-400';
      case 'RECONNECTING':
        return 'bg-amber-400 animate-ping';
      case 'DISCONNECTED':
        return 'bg-red-500';
    }
  };

  return (
    <header className="border-b border-space-600 bg-space-800/90 backdrop-blur sticky top-0 z-50 px-4 py-2.5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left: Brand Identity & Simulation Banner */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-500 to-blue-700 flex items-center justify-center font-bold text-white shadow-lg">
              <Cpu className="w-5 h-5 text-cyan-200" />
            </div>
            <div>
              <span className="font-bold tracking-wider text-base text-white">AURORA</span>
              <span className="text-xs text-slate-400 ml-1.5 hidden sm:inline">OPS WORKBENCH</span>
            </div>
          </div>

          {/* Persistent Simulation Warning Badge (Never hidden on ops pages) */}
          <div className="flex items-center bg-amber-500/15 border border-amber-500/40 px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold text-amber-300">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse mr-1.5" />
            SIMULATION ONLY
          </div>
        </div>

        {/* Center: Flight Mode & Simulation Run Metadata */}
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
          {/* Mode Pill */}
          <div className={`px-2.5 py-1 rounded border font-semibold flex items-center gap-1.5 ${getModeBadgeClass(currentMode)}`}>
            {currentMode === 'SAFE_MODE' && <ShieldAlert className="w-3.5 h-3.5" />}
            <span>MODE: {currentMode}</span>
          </div>

          {/* Run ID */}
          <div className="bg-space-700 border border-space-600 px-2.5 py-1 rounded text-slate-300 hidden md:block">
            RUN: <span className="text-cyan-400">{simStatus?.run_id ? simStatus.run_id.slice(0, 8) : 'IDLE'}</span>
          </div>

          {/* Sim Clock */}
          <div className="bg-space-700 border border-space-600 px-2.5 py-1 rounded text-slate-300">
            T+ <span className="text-white font-semibold">{telemetry ? telemetry.timestamp_sim.toFixed(1) : '0.0'}s</span>
          </div>
        </div>

        {/* Right: Connection & Health Status */}
        <div className="flex items-center space-x-3 font-mono text-xs">
          {/* Stale Telemetry Indicator */}
          {isStale && (
            <div className="flex items-center bg-red-500/20 text-red-400 border border-red-500/40 px-2 py-0.5 rounded text-[11px]">
              <AlertTriangle className="w-3.5 h-3.5 mr-1" />
              STALE TELEMETRY
            </div>
          )}

          {/* Backend Connection Status */}
          <div className="flex items-center space-x-1.5 bg-space-700/80 border border-space-600 px-2.5 py-1 rounded">
            <span className={`w-2 h-2 rounded-full ${getConnectionDotClass()}`} />
            <span className="text-slate-300 font-medium text-[11px]">{connectionStatus}</span>
          </div>

          {/* Manual Refresh */}
          <button
            onClick={() => refreshAll()}
            title="Refresh backend state"
            className="p-1 rounded bg-space-700 hover:bg-space-600 text-slate-300 hover:text-white transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
};
