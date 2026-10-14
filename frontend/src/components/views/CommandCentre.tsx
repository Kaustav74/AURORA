import React, { useState, useEffect } from 'react';
import { useAurora } from '../../context/AuroraContext';
import { api } from '../../lib/api-client';
import { CommandItem } from '../../types';
import {
  Terminal,
  Send,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  ShieldAlert,
  RefreshCw,
} from 'lucide-react';

export const CommandCentre: React.FC = () => {
  const { spacecraftState, telemetry, refreshAll } = useAurora();
  const currentMode = spacecraftState?.mode || telemetry?.mode || 'STANDBY';

  const [commands, setCommands] = useState<CommandItem[]>([]);
  const [selectedType, setSelectedType] = useState<string>('PING');
  const [targetMode, setTargetMode] = useState<string>('NOMINAL');
  const [paramName, setParamName] = useState<string>('cadence_hz');
  const [paramValue, setParamValue] = useState<string>('1.0');
  const [recoveryReason, setRecoveryReason] = useState<string>('Subsystems cooled below safety boundary.');
  const [operatorId, setOperatorId] = useState<string>('FLIGHT_DIRECTOR_1');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchCommandHistory = async () => {
    try {
      const data = await api.getCommands();
      setCommands(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchCommandHistory();
  }, []);

  const handleSendCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFeedback(null);

    let params: Record<string, any> = {};
    if (selectedType === 'SET_MODE') {
      params = { target_mode: targetMode };
    } else if (selectedType === 'ADJUST_PARAMETER') {
      params = { parameter_name: paramName, value: Number(paramValue) };
    } else if (selectedType === 'RECOVERY_REQUEST') {
      params = { reason: recoveryReason };
    }

    try {
      const idempotencyKey = `CMD-${Date.now()}`;
      const result = await api.submitCommand(selectedType, params, operatorId, idempotencyKey);
      await fetchCommandHistory();
      await refreshAll();

      if (result.status === 'REJECTED') {
        setFeedback({
          type: 'error',
          message: `COMMAND REJECTED: ${result.rejection_reason || 'Validation failed.'}`,
        });
      } else if (result.status === 'FAILED') {
        setFeedback({
          type: 'error',
          message: `COMMAND EXECUTION FAILED: ${result.rejection_reason || 'Subsystem rejected.'}`,
        });
      } else {
        setFeedback({
          type: 'success',
          message: `Command ${result.command_type} (${result.id}) dispatched & ${result.status}.`,
        });
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Transmission error.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white font-mono flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            FLIGHT COMMAND CENTRE
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Two-phase validated command uplink. Commands are verified against flight rules prior to dispatch.
          </p>
        </div>

        <button
          onClick={fetchCommandHistory}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-space-700 hover:bg-space-600 text-slate-300 font-mono text-xs border border-space-500 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>REFRESH LOG</span>
        </button>
      </div>

      {/* Safe Mode Operational Restriction Warning */}
      {currentMode === 'SAFE_MODE' && (
        <div className="p-3.5 rounded-xl border border-amber-500/50 bg-amber-950/20 text-amber-300 font-mono text-xs flex items-start gap-2.5">
          <ShieldAlert className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">SAFE_MODE COMMAND RESTRICTION ENGAGED: </span>
            <span>
              The spacecraft is currently in SAFE_MODE. Arbitrary configuration and payload commands are locked out.
              Only <strong>RECOVERY_REQUEST</strong>, <strong>REQUEST_TELEMETRY</strong>, and <strong>PING</strong> are authorized.
            </span>
          </div>
        </div>
      )}

      {/* Grid: Command Builder & Audit Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Command Form */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-4 font-mono text-xs">
          <h3 className="font-bold text-slate-200 border-b border-space-700 pb-2">
            UPLINK COMMAND BUILDER
          </h3>

          <form onSubmit={handleSendCommand} className="space-y-3">
            <div>
              <label className="text-slate-400 block mb-1">COMMAND ACTION</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="w-full bg-space-700 border border-space-500 rounded p-2 text-slate-200 text-xs focus:border-cyan-400 outline-none"
              >
                <option value="PING">PING (Subsystem Heartbeat)</option>
                <option value="REQUEST_TELEMETRY">REQUEST_TELEMETRY (Snapshot)</option>
                <option value="SET_MODE">SET_MODE (Spacecraft State Machine)</option>
                <option value="ADJUST_PARAMETER">ADJUST_PARAMETER (Tuning)</option>
                <option value="RECOVERY_REQUEST">RECOVERY_REQUEST (Safe Hold Exit)</option>
              </select>
            </div>

            {selectedType === 'SET_MODE' && (
              <div>
                <label className="text-slate-400 block mb-1">TARGET FLIGHT MODE</label>
                <select
                  value={targetMode}
                  onChange={(e) => setTargetMode(e.target.value)}
                  className="w-full bg-space-700 border border-space-500 rounded p-2 text-slate-200 text-xs"
                >
                  <option value="NOMINAL">NOMINAL</option>
                  <option value="DEGRADED">DEGRADED</option>
                  <option value="STANDBY">STANDBY</option>
                  <option value="SAFE_MODE">SAFE_MODE</option>
                </select>
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Note: Direct SAFE_MODE to NOMINAL is strictly rejected by flight software rules.
                </span>
              </div>
            )}

            {selectedType === 'ADJUST_PARAMETER' && (
              <div className="space-y-2">
                <div>
                  <label className="text-slate-400 block mb-1">PARAMETER NAME</label>
                  <select
                    value={paramName}
                    onChange={(e) => setParamName(e.target.value)}
                    className="w-full bg-space-700 border border-space-500 rounded p-2 text-slate-200 text-xs"
                  >
                    <option value="cadence_hz">cadence_hz (Clock rate)</option>
                    <option value="heater_bias_w">heater_bias_w (Thermal bias)</option>
                    <option value="ssr_downlink_rate_kbps">ssr_downlink_rate_kbps (Rate)</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">VALUE</label>
                  <input
                    type="number"
                    step="0.1"
                    value={paramValue}
                    onChange={(e) => setParamValue(e.target.value)}
                    className="w-full bg-space-700 border border-space-500 rounded p-2 text-slate-200 text-xs"
                  />
                </div>
              </div>
            )}

            {selectedType === 'RECOVERY_REQUEST' && (
              <div>
                <label className="text-slate-400 block mb-1">OPERATIONAL JUSTIFICATION</label>
                <textarea
                  rows={2}
                  value={recoveryReason}
                  onChange={(e) => setRecoveryReason(e.target.value)}
                  className="w-full bg-space-700 border border-space-500 rounded p-2 text-slate-200 text-xs"
                />
              </div>
            )}

            <div>
              <label className="text-slate-400 block mb-1">ISSUED BY (CALLSIGN)</label>
              <input
                type="text"
                value={operatorId}
                onChange={(e) => setOperatorId(e.target.value)}
                className="w-full bg-space-700 border border-space-500 rounded p-2 text-slate-200 text-xs font-mono"
              />
            </div>

            {feedback && (
              <div
                className={`p-2.5 rounded border text-[11px] font-mono ${
                  feedback.type === 'success'
                    ? 'border-emerald-500/40 bg-emerald-950/20 text-emerald-300'
                    : 'border-red-500/40 bg-red-950/20 text-red-300'
                }`}
              >
                {feedback.message}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 active:bg-cyan-700 text-white font-bold transition flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{isSubmitting ? 'VALIDATING & DISPATCHING...' : 'DISPATCH COMMAND'}</span>
            </button>
          </form>
        </div>

        {/* Command Audit Log */}
        <div className="lg:col-span-2 bg-space-800 border border-space-600 rounded-xl p-4 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-space-700">
            <h3 className="font-bold text-slate-200">COMMAND LOG & VALIDATION AUDIT</h3>
            <span className="text-slate-500 text-[11px]">Total: {commands.length} attempts</span>
          </div>

          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-space-700 text-slate-500 text-[11px]">
                  <th className="py-2 px-3">CMD_ID</th>
                  <th className="py-2 px-3">TYPE</th>
                  <th className="py-2 px-3">STATUS</th>
                  <th className="py-2 px-3">CALLSIGN</th>
                  <th className="py-2 px-3">DETAILS / REJECTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-space-700/60 text-slate-300">
                {commands.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      No commands issued yet. Use the builder on the left to dispatch flight actions.
                    </td>
                  </tr>
                ) : (
                  commands.map((cmd) => (
                    <tr key={cmd.id} className="hover:bg-space-700/40 transition">
                      <td className="py-2 px-3 font-semibold text-cyan-300">{cmd.id}</td>
                      <td className="py-2 px-3">{cmd.command_type}</td>
                      <td className="py-2 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            cmd.status === 'COMPLETED'
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : cmd.status === 'REJECTED'
                              ? 'bg-red-500/20 text-red-400'
                              : cmd.status === 'FAILED'
                              ? 'bg-red-500/20 text-red-400'
                              : 'bg-amber-500/20 text-amber-400'
                          }`}
                        >
                          {cmd.status}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-slate-400">{cmd.issued_by}</td>
                      <td className="py-2 px-3 text-slate-400 max-w-xs truncate" title={cmd.rejection_reason || JSON.stringify(cmd.parameters)}>
                        {cmd.rejection_reason ? (
                          <span className="text-red-400">{cmd.rejection_reason}</span>
                        ) : (
                          JSON.stringify(cmd.parameters)
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};