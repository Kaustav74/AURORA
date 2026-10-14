import React, { useState } from 'react';
import { PhysicsAnomaly } from '../../../types/physics_lab';
import { AlertTriangle, CheckCircle2, XCircle, RotateCcw, FileText, X } from 'lucide-react';

interface AnomalyInvestigationModalProps {
  anomaly: PhysicsAnomaly | null;
  onClose: () => void;
  onUpdateStatus: (id: string, status: string, notes?: string) => Promise<void>;
  onReproduceInSimulator?: (anomaly: PhysicsAnomaly) => void;
}

export const AnomalyInvestigationModal: React.FC<AnomalyInvestigationModalProps> = ({
  anomaly,
  onClose,
  onUpdateStatus,
  onReproduceInSimulator,
}) => {
  if (!anomaly) return null;

  const [currentStatus, setCurrentStatus] = useState(anomaly.status);
  const [notes, setNotes] = useState(anomaly.resolution_notes || '');
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onUpdateStatus(anomaly.id, currentStatus, notes);
      onClose();
    } finally {
      setIsSaving(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-300 border-red-500/40';
      case 'WARNING':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      default:
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-space-900 border border-space-700 rounded-xl max-w-2xl w-full p-6 space-y-5 shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-space-700 pb-3">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${getSeverityBadge(anomaly.severity)}`}>
                {anomaly.severity}
              </span>
              <span className="text-xs font-mono text-slate-400">
                {anomaly.id} • t = {anomaly.time_sim.toFixed(2)} s
              </span>
            </div>
            <h3 className="text-base font-semibold text-slate-100">{anomaly.title}</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-100 p-1 rounded-lg hover:bg-space-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Detailed Metrics Table */}
        <div className="grid grid-cols-2 gap-3 text-xs font-mono bg-space-950 p-3.5 rounded-lg border border-space-800">
          <div>
            <span className="text-slate-500 block text-[10px]">DETECTION RULE</span>
            <span className="text-cyan-400 font-semibold">{anomaly.detection_rule}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">CATEGORY</span>
            <span className="text-slate-200">{anomaly.category}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">OBSERVED VALUE</span>
            <span className="text-amber-300">{anomaly.observed_value || 'N/A'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">REFERENCE THRESHOLD</span>
            <span className="text-slate-300">{anomaly.threshold || anomaly.reference_value || 'N/A'}</span>
          </div>
        </div>

        {/* Explanation */}
        <div className="space-y-1.5 text-xs">
          <span className="text-slate-400 font-mono font-semibold block text-[11px]">SCIENTIFIC EXPLANATION</span>
          <p className="text-slate-300 leading-relaxed bg-space-850 p-3 rounded-lg border border-space-700/60 font-sans">
            {anomaly.explanation}
          </p>
        </div>

        {/* Recommended Action */}
        {anomaly.recommended_action && (
          <div className="space-y-1.5 text-xs">
            <span className="text-slate-400 font-mono font-semibold block text-[11px]">RECOMMENDED INVESTIGATION ACTION</span>
            <p className="text-amber-200/90 leading-relaxed bg-amber-950/30 border border-amber-500/30 p-2.5 rounded-lg font-sans">
              {anomaly.recommended_action}
            </p>
          </div>
        )}

        {/* Status Workflow Selector & Notes */}
        <div className="space-y-3 border-t border-space-700 pt-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-mono text-slate-300">INVESTIGATION STATUS</label>
            <select
              value={currentStatus}
              onChange={(e) => setCurrentStatus(e.target.value as any)}
              className="bg-space-950 border border-space-700 text-xs font-mono text-slate-200 rounded px-3 py-1.5 focus:border-cyan-500 focus:outline-none"
            >
              <option value="NEW">NEW</option>
              <option value="INVESTIGATING">INVESTIGATING</option>
              <option value="REPRODUCED">REPRODUCED</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="DISMISSED">DISMISSED</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono text-slate-400">RESEARCHER RESOLUTION NOTES</label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record findings, parameter sensitivity, integrator convergence checks..."
              className="w-full bg-space-950 border border-space-700 rounded-lg p-2.5 text-xs text-slate-200 font-mono focus:border-cyan-500 focus:outline-none resize-none"
            />
          </div>
        </div>

        {/* Modal Action Buttons */}
        <div className="flex items-center justify-between border-t border-space-700 pt-3">
          {onReproduceInSimulator ? (
            <button
              onClick={() => {
                onReproduceInSimulator(anomaly);
                onClose();
              }}
              className="flex items-center space-x-1.5 text-xs font-mono text-cyan-400 hover:text-cyan-300 hover:underline"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reproduce in Simulator</span>
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center space-x-2">
            <button
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg text-xs font-mono text-slate-400 hover:text-slate-200 hover:bg-space-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-1.5 rounded-lg text-xs font-mono font-medium bg-cyan-600 hover:bg-cyan-500 text-white transition-colors flex items-center space-x-1.5"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{isSaving ? 'Saving...' : 'Save Anomaly Record'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
