import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api-client';
import { ScenarioItem, ScenarioRunItem } from '../../types';
import {
  FlaskConical,
  Play,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Hash,
} from 'lucide-react';

export const ScenarioLabView: React.FC = () => {
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);
  const [runs, setRuns] = useState<ScenarioRunItem[]>([]);
  const [activeRunningId, setActiveRunningId] = useState<string | null>(null);
  const [latestResult, setLatestResult] = useState<ScenarioRunItem | null>(null);

  const fetchScenariosAndRuns = async () => {
    try {
      const [scList, rList] = await Promise.all([
        api.getScenarios(),
        api.getScenarioRuns(),
      ]);
      setScenarios(scList);
      setRuns(rList);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchScenariosAndRuns();
  }, []);

  const handleRunScenario = async (id: string) => {
    setActiveRunningId(id);
    try {
      const result = await api.runScenario(id);
      setLatestResult(result);
      await fetchScenariosAndRuns();
    } catch (err: any) {
      alert(`Scenario run failed: ${err.message}`);
    } finally {
      setActiveRunningId(null);
    }
  };

  return (
    <div className="space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-cyan-400" />
            SCENARIO LAB & REPRODUCIBLE RUNS
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic flight anomaly scenarios initialized with fixed pseudo-random seeds.
          </p>
        </div>

        <button
          onClick={fetchScenariosAndRuns}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-space-700 hover:bg-space-600 text-slate-300 border border-space-500 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>REFRESH</span>
        </button>
      </div>

      {/* Latest Scenario Run Execution Result */}
      {latestResult && (
        <div className="p-4 rounded-xl border border-cyan-500/40 bg-space-800 space-y-3">
          <div className="flex items-center justify-between border-b border-space-700 pb-2">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-white text-sm">
                SCENARIO EXECUTION: {latestResult.scenario_id}
              </span>
              <span className="text-slate-500 text-[11px]">(SEED: {latestResult.seed})</span>
            </div>
            <span
              className={`px-2.5 py-1 rounded text-xs font-bold ${
                latestResult.pass_fail === 'PASS'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                  : 'bg-red-500/20 text-red-400 border border-red-500/40'
              }`}
            >
              RESULT: {latestResult.pass_fail || 'COMPLETED'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-space-900 p-3 rounded border border-space-700 space-y-1.5 text-slate-300">
              <span className="text-slate-400 font-bold block mb-1">OBSERVED OUTCOMES:</span>
              <pre className="text-[11px] text-cyan-300 overflow-x-auto">
                {JSON.stringify(latestResult.observed_outcomes, null, 2)}
              </pre>
            </div>

            <div className="bg-space-900 p-3 rounded border border-space-700 space-y-1.5 text-slate-300">
              <span className="text-slate-400 font-bold block mb-1">DEVIATIONS & AUDIT:</span>
              {latestResult.deviations && latestResult.deviations.length > 0 ? (
                <ul className="list-disc list-inside space-y-1 text-red-400 text-[11px]">
                  {latestResult.deviations.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              ) : (
                <div className="text-emerald-400 text-[11px] flex items-center gap-1.5 py-2">
                  <CheckCircle className="w-4 h-4" />
                  <span>Zero deviations detected. Observed telemetry matched expected bounds exactly.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Available Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios.map((sc) => (
          <div
            key={sc.id}
            className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-col justify-between space-y-3"
          >
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-bold text-cyan-300">{sc.id}</span>
                <span className="text-[10px] bg-space-700 text-slate-400 px-1.5 py-0.5 rounded">
                  SEED: {sc.seed}
                </span>
              </div>
              <h3 className="font-bold text-white text-xs mb-1">{sc.name}</h3>
              <p className="text-slate-400 text-[11px] leading-relaxed">{sc.description}</p>
            </div>

            <div className="pt-2 border-t border-space-700/80 flex items-center justify-between">
              <span className="text-[10px] text-slate-500">
                {sc.fault_schedule.length} fault injections scheduled
              </span>
              <button
                onClick={() => handleRunScenario(sc.id)}
                disabled={activeRunningId !== null}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition disabled:opacity-50"
              >
                <Play className="w-3 h-3" />
                <span>{activeRunningId === sc.id ? 'RUNNING...' : 'EXECUTE'}</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Historical Runs Table */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3">
        <h3 className="font-bold text-slate-200 border-b border-space-700 pb-2">
          HISTORICAL SCENARIO RUN AUDIT LOG
        </h3>

        <div className="overflow-x-auto max-h-72">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-space-700 text-slate-500 text-[11px]">
                <th className="py-2 px-3">RUN_ID</th>
                <th className="py-2 px-3">SCENARIO</th>
                <th className="py-2 px-3">SEED</th>
                <th className="py-2 px-3">STATUS</th>
                <th className="py-2 px-3">OUTCOME</th>
                <th className="py-2 px-3">EXECUTED_AT</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-space-700/60 text-slate-300">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-500">
                    No scenario executions recorded yet.
                  </td>
                </tr>
              ) : (
                runs.map((r) => (
                  <tr key={r.id} className="hover:bg-space-700/40 transition">
                    <td className="py-2 px-3 font-semibold text-cyan-300">{r.id}</td>
                    <td className="py-2 px-3">{r.scenario_id}</td>
                    <td className="py-2 px-3 text-slate-400">{r.seed}</td>
                    <td className="py-2 px-3">{r.status}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          r.pass_fail === 'PASS'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}
                      >
                        {r.pass_fail || 'COMPLETED'}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-400 text-[11px]">
                      {new Date(r.started_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
