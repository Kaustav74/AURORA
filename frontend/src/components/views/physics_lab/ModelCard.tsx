import React, { useState } from 'react';
import { PhysicsModelMeta } from '../../../types/physics_lab';
import { ChevronDown, ChevronUp, CheckCircle, AlertTriangle, ShieldAlert } from 'lucide-react';

interface ModelCardProps {
  model: PhysicsModelMeta;
  isSelected?: boolean;
  onSelect?: (modelId: string) => void;
}

export const ModelCard: React.FC<ModelCardProps> = ({
  model,
  isSelected = false,
  onSelect,
}) => {
  const [expanded, setExpanded] = useState(false);

  const modelName = model.display_name || model.model_name || model.model_id;
  const statusVal = model.implementation_status || model.status || 'OPERATIONAL';
  const equation =
    model.implementation_equation_latex ||
    model.source_equation_raw ||
    model.provenance?.mathematical_definition ||
    'N/A';
  const sourceDoc = model.source_document || model.provenance?.source_document || 'Research Compendium';
  const sourcePages = model.source_page_range || model.provenance?.source_pages || 'N/A';
  const domain = model.domain_of_validity || model.provenance?.domain_of_validity || 'r > 0';
  const limitations = model.known_limitations || model.provenance?.implementation_notes || 'N/A';
  const family = model.formulation_family || model.category || 'GRAVITATION';

  const getStatusBadge = () => {
    if (statusVal.includes('VERIFIED') || statusVal === 'OPERATIONAL') {
      return (
        <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
          <CheckCircle className="w-3 h-3 text-emerald-400" />
          <span>{statusVal}</span>
        </span>
      );
    }
    if (statusVal.includes('EXPERIMENTAL') || statusVal === 'EXPERIMENTAL') {
      return (
        <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
          <AlertTriangle className="w-3 h-3 text-amber-400" />
          <span>{statusVal}</span>
        </span>
      );
    }
    return (
      <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
        <ShieldAlert className="w-3 h-3 text-rose-400" />
        <span>{statusVal}</span>
      </span>
    );
  };

  return (
    <div
      className={`rounded-lg border transition-all ${
        isSelected
          ? 'bg-space-850 border-cyan-500/80 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-500/50'
          : 'bg-space-900 border-space-700/80 hover:border-space-600'
      }`}
    >
      {/* Top Header */}
      <div className="p-4 flex items-start justify-between gap-3">
        <div className="space-y-1.5 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono font-bold text-cyan-400">{model.model_id}</span>
            <span className="text-slate-500 font-mono text-[10px]">v{model.model_version}</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-space-800 text-slate-300 border border-space-700">
              {family}
            </span>
            {getStatusBadge()}
          </div>
          <h4 className="text-sm font-semibold text-slate-100">{modelName}</h4>
          <p className="text-xs text-slate-400 font-mono">
            {sourceDoc} (Pages: {sourcePages})
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {onSelect && (
            <button
              onClick={() => onSelect(model.model_id)}
              className={`px-3 py-1.5 rounded text-xs font-mono font-medium transition-all ${
                isSelected
                  ? 'bg-cyan-500 text-space-950 font-bold'
                  : 'bg-space-800 text-slate-300 hover:bg-space-700 hover:text-white border border-space-700'
              }`}
            >
              {isSelected ? 'Active Model' : 'Select'}
            </button>
          )}

          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded hover:bg-space-800 transition-colors"
            title="Toggle Equation Provenance"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expanded Provenance Details */}
      {expanded && (
        <div className="border-t border-space-700/80 bg-space-950/60 p-4 space-y-3.5 text-xs">
          {/* Mathematical Definition */}
          <div>
            <span className="text-slate-400 font-mono font-bold block text-[10px] uppercase tracking-wider mb-1">
              Mathematical Formulation
            </span>
            <pre className="p-2.5 rounded bg-space-900 border border-space-800 font-mono text-cyan-300 overflow-x-auto whitespace-pre-wrap">
              {equation}
            </pre>
          </div>

          {/* Known Limitations */}
          <div>
            <span className="text-slate-400 font-mono font-bold block text-[10px] uppercase tracking-wider mb-1">
              Domain of Validity & Known Limitations
            </span>
            <p className="text-slate-300 leading-relaxed bg-space-900/60 p-2.5 rounded border border-space-800 font-sans">
              {domain} — {limitations}
            </p>
          </div>

          {/* Conserved Quantities */}
          {model.conserved_quantities && model.conserved_quantities.length > 0 && (
            <div>
              <span className="text-slate-400 font-mono font-bold block text-[10px] uppercase tracking-wider mb-1">
                Conserved Quantities / Invariants
              </span>
              <ul className="list-disc list-inside space-y-1 text-slate-400 pl-1 font-sans">
                {model.conserved_quantities.map((cq, idx) => (
                  <li key={idx}>{cq}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Scientific Validation Status */}
          {model.scientific_validation_status && (
            <div>
              <span className="text-slate-400 font-mono font-bold block text-[10px] uppercase tracking-wider mb-1">
                Empirical Validation Taxonomy
              </span>
              <span className="px-2 py-1 rounded bg-space-900 border border-space-800 font-mono text-amber-300 inline-block">
                {model.scientific_validation_status}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
