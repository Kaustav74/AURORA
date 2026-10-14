import React from 'react';
import {
  Info,
  Cpu,
  Database,
  ShieldAlert,
  Terminal,
  BookOpen,
} from 'lucide-react';

export const SettingsAboutView: React.FC = () => {
  return (
    <div className="space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Info className="w-4 h-4 text-cyan-400" />
            PROJECT AURORA ARCHITECTURE & SIMULATION NOTES
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Autonomous Unified Reconnaissance, Operations & Reliability Architecture (Educational Mission Operations Simulator).
          </p>
        </div>
      </div>

      {/* Prominent Educational / Non-Flight Disclaimer */}
      <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/20 text-amber-300 space-y-1.5 leading-relaxed">
        <div className="font-bold text-sm flex items-center gap-2 text-amber-200">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          SIMULATION SOFTWARE ONLY — IMPORTANT NOTICE
        </div>
        <p>
          Project AURORA is an educational engineering portfolio software simulation designed for learning full-stack software development, flight software concepts, telemetry ingestion, mission operations, fault detection, and systems engineering.
        </p>
        <p className="text-[11px] text-amber-400 font-semibold">
          It is NOT connected to any real spacecraft, NOT certified for flight, NOT qualified for safety-critical aerospace operations, and NOT endorsed by any space agency.
        </p>
      </div>

      {/* Simulation Assumptions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-2">
          <h3 className="font-bold text-white text-xs border-b border-space-700 pb-2 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            SIMULATED SUBSYSTEM MODELS
          </h3>
          <ul className="list-disc list-inside space-y-1.5 text-slate-300 text-[11px] leading-relaxed">
            <li>
              <strong>Thermal Dynamics:</strong> Sinusoidal day/night insolation across a 90-minute simulated orbital period (5400s). Ambient equilibrium temperature oscillates between 22°C and 28°C.
            </li>
            <li>
              <strong>Overheating Limit (75°C):</strong> Fictional avionics package threshold of <strong>75.0°C</strong>. Crossing this limit automatically commands SAFE_MODE and sheds non-essential loads.
            </li>
            <li>
              <strong>Safe Mode Recovery Discipline:</strong> Reducing temperature alone does not auto-restore NOMINAL. Recovery requires explicit operator authorization with verified preconditions (temp &lt; 75°C, battery &gt; 30%, link != LOST).
            </li>
            <li>
              <strong>Electrical Power (EPS):</strong> Unregulated bus modeled at 24.0V + 4.2V * (SoC / 100). Current drops from 3.5A to 1.1A during safe hold load shedding.
            </li>
          </ul>
        </div>

        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-2">
          <h3 className="font-bold text-white text-xs border-b border-space-700 pb-2 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-purple-400" />
            SOFTWARE & PERSISTENCE ARCHITECTURE
          </h3>
          <ul className="list-disc list-inside space-y-1.5 text-slate-300 text-[11px] leading-relaxed">
            <li>
              <strong>Local-First SQLite:</strong> Stored locally at <code>backend/aurora.db</code>. Zero cloud services, Redis, or Docker required for local execution.
            </li>
            <li>
              <strong>Two-Phase Command Verification:</strong> Commands progress through PENDING → VALIDATED / REJECTED → EXECUTING → COMPLETED / FAILED with idempotency keys.
            </li>
            <li>
              <strong>Deterministic Scenarios:</strong> Seeded pseudo-random generation guarantees repeatable behavior for automated regression testing.
            </li>
            <li>
              <strong>Dual Transport:</strong> High-reliability REST endpoints paired with streaming WebSocket updates at configurable cadence.
            </li>
          </ul>
        </div>
      </div>

      {/* Database Backup & Export Instructions */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-2">
        <h3 className="font-bold text-white text-xs border-b border-space-700 pb-2 flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400" />
          LOCAL DATA STORAGE & BACKUP INSTRUCTIONS
        </h3>
        <p className="text-slate-300 text-[11px] leading-relaxed">
          All simulation runs, telemetry frames, event logs, incident audits, and verification test cases are preserved in the local SQLite database.
        </p>
        <div className="p-3 bg-space-900 rounded border border-space-700 space-y-1 text-slate-300">
          <div><strong>Database Path:</strong> <code>d:\AURORA\backend\aurora.db</code></div>
          <div>
            <strong>Manual Backup Command (PowerShell):</strong>{' '}
            <code className="text-cyan-300">Copy-Item -Path "d:\AURORA\backend\aurora.db" -Destination "d:\AURORA\backend\aurora_backup.db"</code>
          </div>
          <div>
            <strong>Database Reset:</strong> Simply delete <code>aurora.db</code>; the application will automatically initialize a fresh database with baseline requirements and scenarios upon next startup.
          </div>
        </div>
      </div>
    </div>
  );
};
