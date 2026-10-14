import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api-client';
import { HealthOverview } from '../../types';
import {
  HeartPulse,
  Activity,
  CheckCircle,
  AlertTriangle,
  ShieldAlert,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Info,
} from 'lucide-react';

export const HealthIntelligenceView: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthOverview | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchHealth = async () => {
    setIsLoading(true);
    try {
      const data = await api.getHealthOverview();
      setHealthData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <HeartPulse className="w-4 h-4 text-emerald-400" />
            SPACECRAFT HEALTH INTELLIGENCE & TELEMETRY DIAGNOSTICS
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Transparent, rule-based subsystem health indexing with rolling statistical baseline tracking.
          </p>
        </div>

        <button
          onClick={fetchHealth}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-space-700 hover:bg-space-600 text-slate-300 border border-space-500 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>EVALUATE</span>
        </button>
      </div>

      {/* Overall Health Score Card */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="text-slate-400 text-xs">OVERALL VEHICLE INTEGRITY INDEX</span>
          <div className="flex items-baseline space-x-3">
            <span className="text-4xl font-bold text-white tracking-tight">
              {healthData ? `${healthData.overall_health_pct.toFixed(1)}%` : '--'}
            </span>
            <span
              className={`px-2.5 py-1 rounded text-xs font-bold ${
                healthData?.overall_status === 'CRITICAL'
                  ? 'bg-red-500/20 text-red-400 border border-red-500/40 glow-red'
                  : healthData?.overall_status === 'DEGRADED'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                  : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
              }`}
            >
              STATUS: {healthData?.overall_status || 'NOMINAL'}
            </span>
          </div>
        </div>

        <div className="max-w-md text-slate-400 text-[11px] leading-relaxed">
          Aggregated health metric across Thermal, Electrical Power, Communications, Attitude Determination, and Data Handling subsystems.
        </div>
      </div>

      {/* Subsystem Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {healthData?.subsystems.map((sub) => (
          <div
            key={sub.name}
            className={`bg-space-800 border rounded-xl p-4 space-y-2.5 transition ${
              sub.status === 'CRITICAL'
                ? 'border-red-500/50 bg-red-950/20'
                : sub.status === 'DEGRADED'
                ? 'border-amber-500/40 bg-amber-950/15'
                : 'border-space-600'
            }`}
          >
            <div className="flex items-center justify-between border-b border-space-700 pb-2">
              <span className="font-bold text-slate-200">{sub.name}</span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  sub.status === 'CRITICAL'
                    ? 'bg-red-500/20 text-red-400'
                    : sub.status === 'DEGRADED'
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'bg-emerald-500/20 text-emerald-400'
                }`}
              >
                {sub.score_pct.toFixed(0)}% • {sub.status}
              </span>
            </div>

            <p className="text-slate-300 text-[11px]">{sub.summary}</p>

            {sub.active_warnings.length > 0 && (
              <div className="space-y-1 pt-1">
                {sub.active_warnings.map((w, idx) => (
                  <div
                    key={idx}
                    className="p-1.5 rounded bg-black/40 border border-red-500/30 text-red-300 text-[10px]"
                  >
                    {w}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Rolling Statistics & Trend Diagnostics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {healthData?.key_metrics.map((m) => (
          <div key={m.metric_name} className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between border-b border-space-700 pb-2">
              <span className="font-bold text-slate-200">{m.metric_name}</span>
              <span className="flex items-center space-x-1 text-slate-400">
                {m.trend_direction === 'INCREASING' ? (
                  <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
                ) : m.trend_direction === 'DECREASING' ? (
                  <TrendingDown className="w-3.5 h-3.5 text-cyan-400" />
                ) : (
                  <Minus className="w-3.5 h-3.5 text-slate-400" />
                )}
                <span className="text-[10px]">{m.trend_direction}</span>
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center py-1">
              <div className="bg-space-900 p-2 rounded">
                <span className="text-[10px] text-slate-500 block">CURRENT</span>
                <span className="font-bold text-white">{m.current_value.toFixed(1)}</span>
              </div>
              <div className="bg-space-900 p-2 rounded">
                <span className="text-[10px] text-slate-500 block">30-FRAME AVG</span>
                <span className="font-bold text-cyan-300">{m.rolling_avg.toFixed(1)}</span>
              </div>
              <div className="bg-space-900 p-2 rounded">
                <span className="text-[10px] text-slate-500 block">MIN / MAX</span>
                <span className="font-bold text-slate-300">
                  {m.min_value.toFixed(1)} / {m.max_value.toFixed(1)}
                </span>
              </div>
            </div>

            {m.explanation && (
              <p className="text-[11px] text-slate-400 pt-1">{m.explanation}</p>
            )}
          </div>
        ))}
      </div>

      {/* Explainable Diagnostic Decision Log */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3">
        <h3 className="font-bold text-slate-200 border-b border-space-700 pb-2 flex items-center gap-2">
          <Info className="w-4 h-4 text-cyan-400" />
          EXPLAINABLE DIAGNOSTIC LOG (FLIGHT OPERATIONS RULES)
        </h3>

        <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
          {healthData?.rule_explanations.map((exp, idx) => (
            <div
              key={idx}
              className="p-2 rounded bg-space-900 border border-space-700/60 text-slate-300 flex items-start space-x-2"
            >
              <CheckCircle className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
              <span>{exp}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
