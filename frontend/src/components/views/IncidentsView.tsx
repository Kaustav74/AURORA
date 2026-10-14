import React, { useState } from 'react';
import { useAurora } from '../../context/AuroraContext';
import { api } from '../../lib/api-client';
import { IncidentItem } from '../../types';
import {
  AlertTriangle,
  ShieldAlert,
  CheckCircle,
  Eye,
  Check,
  RefreshCw,
  X,
} from 'lucide-react';

export const IncidentsView: React.FC = () => {
  const { incidents, refreshAll } = useAurora();
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(null);
  const [resolveReason, setResolveReason] = useState<string>('');
  const [isResolving, setIsResolving] = useState<boolean>(false);
  const [operatorCallsign, setOperatorCallsign] = useState<string>('SYS_CONTROLLER');

  const handleAcknowledge = async (id: string) => {
    try {
      await api.acknowledgeIncident(id, operatorCallsign);
      await refreshAll();
    } catch (err) {
      console.error(err);
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident || !resolveReason.trim()) return;

    setIsResolving(true);
    try {
      await api.resolveIncident(selectedIncident.id, resolveReason, operatorCallsign);
      setSelectedIncident(null);
      setResolveReason('');
      await refreshAll();
    } catch (err) {
      console.error(err);
    } finally {
      setIsResolving(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3 font-mono">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            FAULT DETECTION & INCIDENT MANAGEMENT
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic rule-based fault triggers, telemetry evidence capture, and operational resolution tracking.
          </p>
        </div>

        <button
          onClick={() => refreshAll()}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-space-700 hover:bg-space-600 text-slate-300 text-xs border border-space-500 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>REFRESH</span>
        </button>
      </div>

      {/* Incidents Table */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between pb-2 border-b border-space-700">
          <h3 className="font-bold text-slate-200">ACTIVE & RESOLVED FLIGHT ANOMALIES</h3>
          <span className="text-slate-500 text-[11px]">Total: {incidents.length} recorded</span>
        </div>

        <div className="overflow-x-auto max-h-[500px]">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-space-700 text-slate-500 text-[11px]">
                <th className="py-2 px-3">INCIDENT_ID</th>
                <th className="py-2 px-3">FAULT_TYPE</th>
                <th className="py-2 px-3">SEVERITY</th>
                <th className="py-2 px-3">STATUS</th>
                <th className="py-2 px-3">SUMMARY & EVIDENCE</th>
                <th className="py-2 px-3">TIME</th>
                <th className="py-2 px-3 text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-space-700/60 text-slate-300">
              {incidents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No flight incidents detected. Subsystem metrics nominal.
                  </td>
                </tr>
              ) : (
                incidents.map((inc) => (
                  <tr key={inc.id} className="hover:bg-space-700/40 transition">
                    <td className="py-2 px-3 font-bold text-cyan-300">{inc.id}</td>
                    <td className="py-2 px-3 font-semibold">{inc.fault_type}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          inc.severity === 'CRITICAL'
                            ? 'bg-red-500/20 text-red-400'
                            : 'bg-amber-500/20 text-amber-400'
                        }`}
                      >
                        {inc.severity}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          inc.status === 'RESOLVED'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : inc.status === 'ACKNOWLEDGED'
                            ? 'bg-blue-500/20 text-blue-400'
                            : 'bg-red-500/20 text-red-400 animate-pulse'
                        }`}
                      >
                        {inc.status}
                      </span>
                    </td>
                    <td className="py-2 px-3 max-w-sm truncate" title={inc.details}>
                      {inc.summary}
                    </td>
                    <td className="py-2 px-3 text-slate-400 text-[11px]">
                      T+{inc.first_seen_sim.toFixed(1)}s
                    </td>
                    <td className="py-2 px-3 text-right space-x-2">
                      {inc.status === 'OPEN' && (
                        <button
                          onClick={() => handleAcknowledge(inc.id)}
                          className="px-2 py-1 rounded bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 border border-blue-500/40 transition text-[11px]"
                        >
                          ACKNOWLEDGE
                        </button>
                      )}
                      {inc.status !== 'RESOLVED' && (
                        <button
                          onClick={() => setSelectedIncident(inc)}
                          className="px-2 py-1 rounded bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 border border-emerald-500/40 transition text-[11px]"
                        >
                          RESOLVE
                        </button>
                      )}
                      {inc.status === 'RESOLVED' && (
                        <span className="text-slate-500 text-[11px]">CLOSED</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Resolution Modal */}
      {selectedIncident && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-space-800 border border-space-500 rounded-xl p-5 max-w-lg w-full font-mono text-xs space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-space-700 pb-3">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                RESOLVE FLIGHT INCIDENT: {selectedIncident.id}
              </h3>
              <button
                onClick={() => setSelectedIncident(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-space-900 p-3 rounded border border-space-700 text-slate-300 space-y-1">
              <div><strong>FAULT:</strong> {selectedIncident.fault_type} ({selectedIncident.severity})</div>
              <div><strong>SUMMARY:</strong> {selectedIncident.summary}</div>
              <div className="text-[11px] text-slate-400">{selectedIncident.details}</div>
            </div>

            <form onSubmit={handleResolve} className="space-y-3">
              <div>
                <label className="text-slate-400 block mb-1">
                  OPERATIONAL RESOLUTION JUSTIFICATION (REQUIRED):
                </label>
                <textarea
                  required
                  rows={3}
                  value={resolveReason}
                  onChange={(e) => setResolveReason(e.target.value)}
                  placeholder="Explain corrective procedure, diagnostic check, or recovery precondition satisfied..."
                  className="w-full bg-space-700 border border-space-500 rounded p-2 text-white outline-none focus:border-emerald-400"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">RESOLVED BY (OPERATOR):</label>
                <input
                  type="text"
                  value={operatorCallsign}
                  onChange={(e) => setOperatorCallsign(e.target.value)}
                  className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedIncident(null)}
                  className="px-3 py-1.5 rounded bg-space-700 hover:bg-space-600 text-slate-300 border border-space-600"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={isResolving || !resolveReason.trim()}
                  className="px-4 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition disabled:opacity-50"
                >
                  {isResolving ? 'RECORDING...' : 'CONFIRM RESOLUTION'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
