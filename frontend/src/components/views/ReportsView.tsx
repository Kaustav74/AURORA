import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api-client';
import { MissionReportSummary } from '../../types';
import {
  FileSpreadsheet,
  Download,
  FileText,
  RefreshCw,
  Database,
  ShieldCheck,
} from 'lucide-react';

export const ReportsView: React.FC = () => {
  const [summary, setSummary] = useState<MissionReportSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchSummary = async () => {
    setIsLoading(true);
    try {
      const data = await api.getMissionSummary();
      setSummary(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  return (
    <div className="space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
            ENGINEERING REPORTS & DATA EXPORTS
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Structured flight exports, operational audit trails, and system readiness summaries.
          </p>
        </div>

        <button
          onClick={fetchSummary}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-space-700 hover:bg-space-600 text-slate-300 border border-space-500 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>REFRESH SUMMARY</span>
        </button>
      </div>

      {/* Mission Summary Card */}
      {summary && (
        <div className="bg-space-800 border border-space-600 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-space-700 pb-3">
            <h3 className="font-bold text-white text-sm">
              MISSION OPERATIONS SUMMARY REPORT
            </h3>
            <span className="text-slate-400 text-[11px]">
              GENERATED: {new Date(summary.generated_at).toLocaleString()}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
            <div className="bg-space-900 p-3 rounded border border-space-700">
              <span className="text-slate-500 text-[10px] block">SIMULATION CLOCK</span>
              <span className="text-xl font-bold text-cyan-300">
                T+{summary.simulation_time_seconds.toFixed(1)}s
              </span>
            </div>
            <div className="bg-space-900 p-3 rounded border border-space-700">
              <span className="text-slate-500 text-[10px] block">FLIGHT MODE</span>
              <span className="text-xl font-bold text-white">
                {summary.spacecraft_mode}
              </span>
            </div>
            <div className="bg-space-900 p-3 rounded border border-space-700">
              <span className="text-slate-500 text-[10px] block">STORED FRAMES</span>
              <span className="text-xl font-bold text-emerald-400">
                {summary.total_telemetry_frames}
              </span>
            </div>
            <div className="bg-space-900 p-3 rounded border border-space-700">
              <span className="text-slate-500 text-[10px] block">AUDIT EVENTS</span>
              <span className="text-xl font-bold text-purple-300">
                {summary.total_events}
              </span>
            </div>
          </div>

          <div className="bg-space-900 p-3.5 rounded border border-space-700 space-y-2">
            <span className="font-bold text-slate-300 block">KEY OPERATIONS HIGHLIGHTS:</span>
            <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px]">
              {summary.notes.map((note, idx) => (
                <li key={idx}>{note}</li>
              ))}
              <li>Active incidents: {summary.open_incidents} (Resolved: {summary.resolved_incidents})</li>
              <li>Commands logged: {summary.total_commands}</li>
            </ul>
          </div>

          <div className="p-3 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[11px]">
            <strong>DISCLAIMER:</strong> {summary.disclaimer}
          </div>
        </div>
      )}

      {/* CSV Downloads Hub */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3">
        <h3 className="font-bold text-slate-200 border-b border-space-700 pb-2 flex items-center gap-2">
          <Download className="w-4 h-4 text-cyan-400" />
          ONE-CLICK ENGINEERING EXPORT DOWNLOADS
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
          <a
            href="/api/v1/telemetry/export/csv"
            download
            className="p-3 rounded-lg bg-space-700 hover:bg-space-600 border border-space-500 flex flex-col justify-between transition group"
          >
            <div>
              <span className="font-bold text-white group-hover:text-cyan-300 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-cyan-400" />
                TELEMETRY CSV
              </span>
              <p className="text-slate-400 text-[11px] mt-1">
                Full time-series records: temperatures, power, link quality, ADCS.
              </p>
            </div>
            <span className="text-cyan-400 text-[10px] font-bold mt-3">DOWNLOAD CSV →</span>
          </a>

          <a
            href="/api/v1/events/export/csv"
            download
            className="p-3 rounded-lg bg-space-700 hover:bg-space-600 border border-space-500 flex flex-col justify-between transition group"
          >
            <div>
              <span className="font-bold text-white group-hover:text-cyan-300 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-purple-400" />
                EVENT AUDIT CSV
              </span>
              <p className="text-slate-400 text-[11px] mt-1">
                Sequential event stream: lifecycle triggers, mode switches, alarms.
              </p>
            </div>
            <span className="text-cyan-400 text-[10px] font-bold mt-3">DOWNLOAD CSV →</span>
          </a>

          <a
            href="/api/v1/reports/commands/csv"
            download
            className="p-3 rounded-lg bg-space-700 hover:bg-space-600 border border-space-500 flex flex-col justify-between transition group"
          >
            <div>
              <span className="font-bold text-white group-hover:text-cyan-300 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-emerald-400" />
                COMMANDS CSV
              </span>
              <p className="text-slate-400 text-[11px] mt-1">
                Uplink commands, operator callsigns, validation results and errors.
              </p>
            </div>
            <span className="text-cyan-400 text-[10px] font-bold mt-3">DOWNLOAD CSV →</span>
          </a>

          <a
            href="/api/v1/systems-engineering/traceability/csv"
            download
            className="p-3 rounded-lg bg-space-700 hover:bg-space-600 border border-space-500 flex flex-col justify-between transition group"
          >
            <div>
              <span className="font-bold text-white group-hover:text-cyan-300 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-amber-400" />
                TRACEABILITY CSV
              </span>
              <p className="text-slate-400 text-[11px] mt-1">
                Requirements matrix mapped to verification test evidence.
              </p>
            </div>
            <span className="text-cyan-400 text-[10px] font-bold mt-3">DOWNLOAD CSV →</span>
          </a>
        </div>
      </div>
    </div>
  );
};
