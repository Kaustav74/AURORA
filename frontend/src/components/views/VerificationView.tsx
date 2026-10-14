import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api-client';
import { VerificationCaseItem } from '../../types';
import {
  CheckCircle2,
  XCircle,
  Clock,
  Play,
  FileCheck,
  RefreshCw,
  X,
  AlertCircle,
} from 'lucide-react';

export const VerificationView: React.FC = () => {
  const [cases, setCases] = useState<VerificationCaseItem[]>([]);
  const [selectedCase, setSelectedCase] = useState<VerificationCaseItem | null>(null);
  const [execStatus, setExecStatus] = useState<string>('PASS');
  const [evidenceSummary, setEvidenceSummary] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchCases = async () => {
    setIsLoading(true);
    try {
      const data = await api.getVerificationCases();
      setCases(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleRecordExecution = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase || !evidenceSummary.trim()) return;

    setIsSubmitting(true);
    try {
      await api.executeVerificationCase(selectedCase.id, execStatus, evidenceSummary);
      setSelectedCase(null);
      setEvidenceSummary('');
      await fetchCases();
    } catch (err: any) {
      alert(`Error saving test execution: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const passedCount = cases.filter((c) => c.latest_status === 'PASS').length;
  const failedCount = cases.filter((c) => c.latest_status === 'FAIL').length;
  const notRunCount = cases.filter((c) => c.latest_status === 'NOT RUN').length;
  const blockedCount = cases.filter((c) => c.latest_status === 'BLOCKED').length;

  return (
    <div className="space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            VERIFICATION & TEST EVIDENCE REPOSITORY
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Truthful traceability between requirements and executed test evidence. Tests not executed remain NOT RUN.
          </p>
        </div>

        <button
          onClick={fetchCases}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-space-700 hover:bg-space-600 text-slate-300 border border-space-500 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>REFRESH CASES</span>
        </button>
      </div>

      {/* KPI Counters */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-space-800 border border-emerald-500/40 p-3.5 rounded-xl text-center">
          <span className="text-slate-400 text-[10px] block mb-1">PASSED EVIDENCE</span>
          <span className="text-2xl font-bold text-emerald-400">{passedCount}</span>
        </div>
        <div className="bg-space-800 border border-red-500/40 p-3.5 rounded-xl text-center">
          <span className="text-slate-400 text-[10px] block mb-1">FAILED</span>
          <span className="text-2xl font-bold text-red-400">{failedCount}</span>
        </div>
        <div className="bg-space-800 border border-space-600 p-3.5 rounded-xl text-center">
          <span className="text-slate-400 text-[10px] block mb-1">NOT RUN</span>
          <span className="text-2xl font-bold text-slate-400">{notRunCount}</span>
        </div>
        <div className="bg-space-800 border border-amber-500/40 p-3.5 rounded-xl text-center">
          <span className="text-slate-400 text-[10px] block mb-1">BLOCKED</span>
          <span className="text-2xl font-bold text-amber-400">{blockedCount}</span>
        </div>
      </div>

      {/* Verification Cases Table */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-space-700">
          <h3 className="font-bold text-slate-200">VERIFICATION TEST SUITE</h3>
          <span className="text-slate-500 text-[11px]">Total: {cases.length} cases</span>
        </div>

        <div className="overflow-x-auto max-h-[500px]">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-space-700 text-slate-500 text-[11px]">
                <th className="py-2 px-3">CASE_ID</th>
                <th className="py-2 px-3">TEST TITLE & PURPOSE</th>
                <th className="py-2 px-3">LINKED REQS</th>
                <th className="py-2 px-3">LATEST STATUS</th>
                <th className="py-2 px-3">EVIDENCE SUMMARY</th>
                <th className="py-2 px-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-space-700/60 text-slate-300">
              {cases.map((c) => (
                <tr key={c.id} className="hover:bg-space-700/40 transition">
                  <td className="py-2 px-3 font-bold text-cyan-300">{c.id}</td>
                  <td className="py-2 px-3 max-w-sm">
                    <div className="font-semibold text-white">{c.title}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{c.purpose}</div>
                  </td>
                  <td className="py-2 px-3 text-slate-400">
                    {c.linked_requirement_ids.join(', ')}
                  </td>
                  <td className="py-2 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        c.latest_status === 'PASS'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : c.latest_status === 'FAIL'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : c.latest_status === 'BLOCKED'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-slate-700 text-slate-400'
                      }`}
                    >
                      {c.latest_status}
                    </span>
                  </td>
                  <td className="py-2 px-3 max-w-xs text-slate-400 text-[11px] truncate" title={c.evidence_summary || ''}>
                    {c.evidence_summary || 'No execution run recorded yet'}
                  </td>
                  <td className="py-2 px-3 text-right">
                    <button
                      onClick={() => {
                        setSelectedCase(c);
                        setExecStatus(c.latest_status === 'PASS' ? 'PASS' : 'PASS');
                        setEvidenceSummary(c.evidence_summary || '');
                      }}
                      className="px-2.5 py-1 rounded bg-cyan-600/30 hover:bg-cyan-600/50 text-cyan-300 border border-cyan-500/40 transition text-[11px]"
                    >
                      RECORD EVIDENCE
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Record Execution Modal */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-space-800 border border-space-500 rounded-xl p-5 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-space-700 pb-3">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-cyan-400" />
                RECORD TEST EVIDENCE: {selectedCase.id}
              </h3>
              <button onClick={() => setSelectedCase(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-space-900 p-3 rounded border border-space-700 space-y-1 text-slate-300">
              <div><strong>TITLE:</strong> {selectedCase.title}</div>
              <div><strong>LINKED REQUIREMENTS:</strong> {selectedCase.linked_requirement_ids.join(', ')}</div>
              <div><strong>EXPECTED RESULT:</strong> {selectedCase.expected_result}</div>
            </div>

            <form onSubmit={handleRecordExecution} className="space-y-3">
              <div>
                <label className="text-slate-400 block mb-1">VERIFICATION OUTCOME STATUS</label>
                <select
                  value={execStatus}
                  onChange={(e) => setExecStatus(e.target.value)}
                  className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                >
                  <option value="PASS">PASS (Verified with evidence)</option>
                  <option value="FAIL">FAIL (Observed deviation or defect)</option>
                  <option value="BLOCKED">BLOCKED (Prerequisite missing)</option>
                  <option value="NOT RUN">NOT RUN (Reset to unexecuted)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">
                  OBSERVED EVIDENCE SUMMARY (OUTPUT LOGS, TEST RESULT):
                </label>
                <textarea
                  required
                  rows={3}
                  value={evidenceSummary}
                  onChange={(e) => setEvidenceSummary(e.target.value)}
                  placeholder="e.g. Executed automated pytest test_overheating_slice.py: passed in 0.08s."
                  className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedCase(null)}
                  className="px-3 py-1.5 rounded bg-space-700 hover:bg-space-600 text-slate-300"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !evidenceSummary.trim()}
                  className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition disabled:opacity-50"
                >
                  {isSubmitting ? 'SAVING...' : 'SAVE TEST EVIDENCE'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
