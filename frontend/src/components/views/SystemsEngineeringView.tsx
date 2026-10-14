import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api-client';
import {
  RequirementItem,
  RiskItem,
  DecisionItem,
  InterfaceItem,
  IssueItem,
  ReadinessSummary,
} from '../../types';
import {
  Workflow,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Layers,
  Bug,
  Download,
  RefreshCw,
} from 'lucide-react';

export const SystemsEngineeringView: React.FC = () => {
  const [subTab, setSubTab] = useState<'requirements' | 'risks' | 'adrs' | 'icds' | 'issues' | 'readiness'>('requirements');
  const [requirements, setRequirements] = useState<RequirementItem[]>([]);
  const [risks, setRisks] = useState<RiskItem[]>([]);
  const [decisions, setDecisions] = useState<DecisionItem[]>([]);
  const [interfaces, setInterfaces] = useState<InterfaceItem[]>([]);
  const [issues, setIssues] = useState<IssueItem[]>([]);
  const [readiness, setReadiness] = useState<ReadinessSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchAll = async () => {
    setIsLoading(true);
    try {
      const [reqs, rks, decs, icds, isss, read] = await Promise.all([
        api.getRequirements(),
        api.getRisks(),
        api.getDecisions(),
        api.getInterfaces(),
        api.getIssues(),
        api.getReadinessSummary(),
      ]);
      setRequirements(reqs);
      setRisks(rks);
      setDecisions(decs);
      setInterfaces(icds);
      setIssues(isss);
      setReadiness(read);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const handleExportTraceability = () => {
    window.open('/api/v1/systems-engineering/traceability/csv', '_blank');
  };

  return (
    <div className="space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Workflow className="w-4 h-4 text-cyan-400" />
            SYSTEMS ENGINEERING WORKBENCH
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Mission requirements traceability, risk registers, architecture decisions (ADRs), interface control (ICDs) and system readiness.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleExportTraceability}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-600/30 hover:bg-cyan-600/50 text-cyan-300 border border-cyan-500/40 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>EXPORT MATRIX CSV</span>
          </button>
          <button
            onClick={fetchAll}
            className="p-1.5 rounded bg-space-700 hover:bg-space-600 text-slate-300 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Workbench Subnavigation */}
      <div className="flex space-x-1 bg-space-800 p-1 rounded-lg border border-space-700 overflow-x-auto scrollbar-none">
        {[
          { id: 'requirements', label: `Requirements (${requirements.length})` },
          { id: 'readiness', label: 'Readiness Report' },
          { id: 'risks', label: `Risk Register (${risks.length})` },
          { id: 'adrs', label: `Decisions / ADRs (${decisions.length})` },
          { id: 'icds', label: `Interfaces / ICDs (${interfaces.length})` },
          { id: 'issues', label: `Issues (${issues.length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSubTab(tab.id as any)}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition ${
              subTab === tab.id
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* SUBTAB: Requirements */}
      {subTab === 'requirements' && (
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-space-700">
            <h3 className="font-bold text-slate-200">MISSION REQUIREMENTS REGISTRY</h3>
            <span className="text-cyan-400">
              Coverage: {readiness ? `${readiness.requirement_coverage_pct}%` : '--'}
            </span>
          </div>

          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-space-700 text-slate-500 text-[11px]">
                  <th className="py-2 px-3">REQ_ID</th>
                  <th className="py-2 px-3">TITLE & STATEMENT</th>
                  <th className="py-2 px-3">CATEGORY</th>
                  <th className="py-2 px-3">PRIORITY</th>
                  <th className="py-2 px-3">VERIFICATION METHOD</th>
                  <th className="py-2 px-3">VERIFICATION STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-space-700/60 text-slate-300">
                {requirements.map((r) => (
                  <tr key={r.id} className="hover:bg-space-700/40 transition">
                    <td className="py-2 px-3 font-bold text-cyan-300">{r.id}</td>
                    <td className="py-2 px-3 max-w-md">
                      <div className="font-semibold text-white">{r.title}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{r.statement}</div>
                    </td>
                    <td className="py-2 px-3 text-slate-400">{r.category}</td>
                    <td className="py-2 px-3 font-bold text-slate-300">{r.priority}</td>
                    <td className="py-2 px-3 text-slate-400">{r.verification_method}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.verification_status === 'PASS'
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : r.verification_status === 'FAIL'
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                            : 'bg-slate-700 text-slate-400'
                        }`}
                      >
                        {r.verification_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUBTAB: Readiness Report */}
      {subTab === 'readiness' && readiness && (
        <div className="space-y-4">
          <div className="bg-space-800 border border-space-600 rounded-xl p-5 space-y-4">
            <h3 className="font-bold text-white text-sm border-b border-space-700 pb-2">
              SYSTEM READINESS ASSESSMENT
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
              <div className="bg-space-900 p-3 rounded border border-space-700">
                <span className="text-slate-500 text-[10px] block">REQUIREMENT COVERAGE</span>
                <span className="text-2xl font-bold text-cyan-300">
                  {readiness.requirement_coverage_pct}%
                </span>
              </div>
              <div className="bg-space-900 p-3 rounded border border-space-700">
                <span className="text-slate-500 text-[10px] block">VERIFICATION CASES PASSED</span>
                <span className="text-2xl font-bold text-emerald-400">
                  {readiness.cases_passed} / {readiness.total_verification_cases}
                </span>
              </div>
              <div className="bg-space-900 p-3 rounded border border-space-700">
                <span className="text-slate-500 text-[10px] block">OPEN RISKS</span>
                <span className="text-2xl font-bold text-amber-400">
                  {readiness.open_risks_count}
                </span>
              </div>
              <div className="bg-space-900 p-3 rounded border border-space-700">
                <span className="text-slate-500 text-[10px] block">OPEN DEFECTS / ISSUES</span>
                <span className="text-2xl font-bold text-slate-300">
                  {readiness.open_issues_count}
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded bg-space-900 border border-space-700 text-slate-300">
              <span className="font-bold text-cyan-300 block mb-1">READINESS DIAGNOSTIC:</span>
              <p className="leading-relaxed">{readiness.readiness_assessment}</p>
            </div>

            <div className="p-3 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[11px]">
              <strong>LEGAL & SAFETY DISCLAIMER: </strong> {readiness.disclaimer}
            </div>
          </div>
        </div>
      )}

      {/* SUBTAB: Risks */}
      {subTab === 'risks' && (
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3">
          <h3 className="font-bold text-slate-200 border-b border-space-700 pb-2">
            MISSION RISK MATRIX
          </h3>

          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-space-700 text-slate-500 text-[11px]">
                  <th className="py-2 px-3">RISK_ID</th>
                  <th className="py-2 px-3">DESCRIPTION</th>
                  <th className="py-2 px-3">LIKELIHOOD</th>
                  <th className="py-2 px-3">IMPACT</th>
                  <th className="py-2 px-3">SCORE</th>
                  <th className="py-2 px-3">MITIGATION STRATEGY</th>
                  <th className="py-2 px-3">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-space-700/60 text-slate-300">
                {risks.map((rk) => (
                  <tr key={rk.id} className="hover:bg-space-700/40 transition">
                    <td className="py-2 px-3 font-bold text-amber-400">{rk.id}</td>
                    <td className="py-2 px-3 max-w-sm">{rk.description}</td>
                    <td className="py-2 px-3">{rk.likelihood}/5</td>
                    <td className="py-2 px-3">{rk.impact}/5</td>
                    <td className="py-2 px-3 font-bold text-white">{rk.score}</td>
                    <td className="py-2 px-3 text-slate-400 text-[11px] max-w-sm">{rk.mitigation}</td>
                    <td className="py-2 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-700 text-slate-300">
                        {rk.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUBTAB: ADRs */}
      {subTab === 'adrs' && (
        <div className="space-y-3">
          {decisions.map((adr) => (
            <div key={adr.id} className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between border-b border-space-700 pb-2">
                <span className="font-bold text-cyan-300">{adr.id}: {adr.title}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400">
                  {adr.status}
                </span>
              </div>
              <div className="text-slate-300 space-y-1">
                <div><strong className="text-slate-500">CONTEXT:</strong> {adr.context}</div>
                <div><strong className="text-slate-500">DECISION:</strong> {adr.decision}</div>
                <div><strong className="text-slate-500">ALTERNATIVES CONSIDERED:</strong> {adr.alternatives}</div>
                <div><strong className="text-slate-500">CONSEQUENCES:</strong> {adr.consequences}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* SUBTAB: ICDs */}
      {subTab === 'icds' && (
        <div className="space-y-3">
          {interfaces.map((icd) => (
            <div key={icd.id} className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between border-b border-space-700 pb-2">
                <span className="font-bold text-purple-300">{icd.id}: {icd.name}</span>
                <span className="text-[11px] text-slate-500">v{icd.version}</span>
              </div>
              <div className="text-slate-300 space-y-1">
                <div><strong className="text-slate-500">PRODUCER → CONSUMER:</strong> {icd.producer} → {icd.consumer}</div>
                <div><strong className="text-slate-500">SPECIFICATION:</strong> {icd.contract_spec}</div>
                <div><strong className="text-slate-500">KNOWN LIMITATIONS:</strong> {icd.limitations}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* SUBTAB: Issues */}
      {subTab === 'issues' && (
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3">
          <h3 className="font-bold text-slate-200 border-b border-space-700 pb-2">
            ENGINEERING ISSUE & DEFECT REGISTER
          </h3>
          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-space-700 text-slate-500 text-[11px]">
                  <th className="py-2 px-3">ISSUE_ID</th>
                  <th className="py-2 px-3">TITLE & DESCRIPTION</th>
                  <th className="py-2 px-3">SEVERITY</th>
                  <th className="py-2 px-3">MODULE</th>
                  <th className="py-2 px-3">STATUS</th>
                  <th className="py-2 px-3">RESOLUTION NOTES</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-space-700/60 text-slate-300">
                {issues.map((iss) => (
                  <tr key={iss.id} className="hover:bg-space-700/40 transition">
                    <td className="py-2 px-3 font-bold text-cyan-300">{iss.id}</td>
                    <td className="py-2 px-3 max-w-sm">
                      <div className="font-semibold text-white">{iss.title}</div>
                      <div className="text-[11px] text-slate-400">{iss.description}</div>
                    </td>
                    <td className="py-2 px-3">{iss.severity}</td>
                    <td className="py-2 px-3 text-slate-400">{iss.related_module}</td>
                    <td className="py-2 px-3 font-bold text-emerald-400">{iss.status}</td>
                    <td className="py-2 px-3 text-slate-400 text-[11px] max-w-xs">{iss.resolution_notes || '--'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
