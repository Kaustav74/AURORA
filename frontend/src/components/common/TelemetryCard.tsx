import React from 'react';

interface TelemetryCardProps {
  label: string;
  value: string | number;
  unit?: string;
  status?: 'NOMINAL' | 'CAUTION' | 'CRITICAL' | 'INFO';
  subtext?: string;
  threshold?: string;
}

export const TelemetryCard: React.FC<TelemetryCardProps> = ({
  label,
  value,
  unit,
  status = 'NOMINAL',
  subtext,
  threshold,
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'CRITICAL':
        return 'border-red-500/50 bg-red-950/20 text-red-400';
      case 'CAUTION':
        return 'border-amber-500/40 bg-amber-950/20 text-amber-300';
      case 'NOMINAL':
        return 'border-space-600 bg-space-800/80 text-emerald-400';
      default:
        return 'border-space-600 bg-space-800/80 text-cyan-400';
    }
  };

  return (
    <div className={`p-3.5 rounded-lg border transition-all ${getStatusColor()}`}>
      <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-1">
        <span>{label}</span>
        {threshold && <span className="text-[10px] text-slate-400">{threshold}</span>}
      </div>
      <div className="flex items-baseline space-x-1.5">
        <span className="text-2xl font-bold font-mono tracking-tight text-white">{value}</span>
        {unit && <span className="text-xs font-mono text-slate-300">{unit}</span>}
      </div>
      {subtext && <div className="mt-1 text-[11px] text-slate-400 font-mono">{subtext}</div>}
    </div>
  );
};
