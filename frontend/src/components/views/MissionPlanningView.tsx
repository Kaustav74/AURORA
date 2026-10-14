import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api-client';
import { MissionTaskItem, ScheduleResponse } from '../../types';
import {
  Calendar,
  Plus,
  Play,
  AlertTriangle,
  CheckCircle,
  Clock,
  Trash2,
  RefreshCw,
  GitCommit,
  X,
} from 'lucide-react';

export const MissionPlanningView: React.FC = () => {
  const [tasks, setTasks] = useState<MissionTaskItem[]>([]);
  const [scheduleResult, setScheduleResult] = useState<ScheduleResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isScheduling, setIsScheduling] = useState<boolean>(false);
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);

  // New task form state
  const [newId, setNewId] = useState<string>('TSK-');
  const [newTitle, setNewTitle] = useState<string>('');
  const [newDesc, setNewDesc] = useState<string>('');
  const [newPriority, setNewPriority] = useState<number>(2);
  const [newDuration, setNewDuration] = useState<number>(30);
  const [newEarliestStart, setNewEarliestStart] = useState<number>(0);
  const [newDeadline, setNewDeadline] = useState<string>('');
  const [newDeps, setNewDeps] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);

  const fetchTasks = async () => {
    setIsLoading(true);
    try {
      const data = await api.getTasks();
      setTasks(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleGenerateSchedule = async () => {
    setIsScheduling(true);
    try {
      const result = await api.generateSchedule();
      setScheduleResult(result);
      setTasks(result.tasks);
    } catch (err: any) {
      alert(`Scheduling error: ${err.message}`);
    } finally {
      setIsScheduling(false);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const depsList = newDeps
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    try {
      await api.createTask({
        id: newId.trim(),
        title: newTitle.trim(),
        description: newDesc.trim(),
        priority: Number(newPriority),
        duration_minutes: Number(newDuration),
        earliest_start_minutes: Number(newEarliestStart),
        deadline_minutes: newDeadline.trim() ? Number(newDeadline) : undefined,
        dependencies: depsList,
      });

      setIsCreateOpen(false);
      setNewId(`TSK-0${tasks.length + 1}`);
      setNewTitle('');
      setNewDesc('');
      setNewDeps('');
      await fetchTasks();
    } catch (err: any) {
      setFormError(err.message || 'Failed to create task.');
    }
  };

  const handleDeleteTask = async (id: string) => {
    if (!confirm(`Delete task ${id}?`)) return;
    try {
      await api.deleteTask(id);
      await fetchTasks();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Calendar className="w-4 h-4 text-cyan-400" />
            MISSION PLANNING & TASK SCHEDULER
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            DAG dependency graph validation, cycle detection, and heuristic timeline generation.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsCreateOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>NEW TASK</span>
          </button>
          <button
            onClick={handleGenerateSchedule}
            disabled={isScheduling || tasks.length === 0}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{isScheduling ? 'SOLVING DAG...' : 'GENERATE SCHEDULE'}</span>
          </button>
        </div>
      </div>

      {/* Conflict / Cycle Warning Banner */}
      {scheduleResult && !scheduleResult.success && (
        <div className="p-4 rounded-xl border border-red-500/60 bg-red-950/40 text-red-300 space-y-2">
          <div className="flex items-center space-x-2 font-bold text-red-200">
            <AlertTriangle className="w-4 h-4" />
            <span>SCHEDULE GENERATION CONFLICT DETECTED</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-[11px] text-red-300">
            {scheduleResult.conflicts.map((c, idx) => (
              <li key={idx}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Schedule Success Summary */}
      {scheduleResult && scheduleResult.success && (
        <div className="p-3.5 rounded-xl border border-emerald-500/40 bg-emerald-950/20 text-emerald-300 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span>
              Schedule Solved Nominally: {scheduleResult.scheduled_tasks} tasks scheduled across {scheduleResult.makespan_minutes}m makespan.
            </span>
          </div>
          <span className="text-[11px] bg-black/40 px-2 py-0.5 rounded">
            Heuristic: Topological Precedence + Earliest Deadline First
          </span>
        </div>
      )}

      {/* Tasks Table */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-space-700">
          <h3 className="font-bold text-slate-200">MISSION TASK REGISTRY</h3>
          <span className="text-slate-500 text-[11px]">Tasks: {tasks.length}</span>
        </div>

        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-space-700 text-slate-500 text-[11px]">
                <th className="py-2 px-3">TASK_ID</th>
                <th className="py-2 px-3">TITLE</th>
                <th className="py-2 px-3">PRIORITY</th>
                <th className="py-2 px-3">DURATION</th>
                <th className="py-2 px-3">DEPENDENCIES</th>
                <th className="py-2 px-3">DEADLINE</th>
                <th className="py-2 px-3">STATUS</th>
                <th className="py-2 px-3">SCHEDULE</th>
                <th className="py-2 px-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-space-700/60 text-slate-300">
              {tasks.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    No mission tasks defined. Create tasks to build operational schedules.
                  </td>
                </tr>
              ) : (
                tasks.map((t) => (
                  <tr key={t.id} className="hover:bg-space-700/40 transition">
                    <td className="py-2 px-3 font-bold text-cyan-300">{t.id}</td>
                    <td className="py-2 px-3 font-semibold">{t.title}</td>
                    <td className="py-2 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        t.priority === 1 ? 'bg-red-500/20 text-red-400' : 'bg-slate-700 text-slate-300'
                      }`}>
                        P{t.priority}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-400">{t.duration_minutes}m</td>
                    <td className="py-2 px-3 text-slate-400">
                      {t.dependencies.length > 0 ? t.dependencies.join(', ') : 'None'}
                    </td>
                    <td className="py-2 px-3 text-slate-400">
                      {t.deadline_minutes ? `T+${t.deadline_minutes}m` : 'None'}
                    </td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          t.status === 'SCHEDULED'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : t.status === 'BLOCKED'
                            ? 'bg-red-500/20 text-red-400'
                            : 'bg-amber-500/20 text-amber-400'
                        }`}
                      >
                        {t.status}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-300">
                      {t.scheduled_start_minutes !== null && t.scheduled_start_minutes !== undefined ? (
                        <span>T+{t.scheduled_start_minutes}m → T+{t.scheduled_end_minutes}m</span>
                      ) : (
                        <span className="text-slate-500">{t.scheduling_notes || 'Pending replan'}</span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-right">
                      <button
                        onClick={() => handleDeleteTask(t.id)}
                        className="text-slate-500 hover:text-red-400 transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Visual Gantt Timeline */}
      {scheduleResult && scheduleResult.success && (
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3">
          <h3 className="font-bold text-slate-200">GANTT SCHEDULE TIMELINE</h3>
          <div className="space-y-2 pt-2">
            {tasks
              .filter((t) => t.status === 'SCHEDULED')
              .map((t) => {
                const totalSpan = Math.max(1, scheduleResult.makespan_minutes);
                const leftPct = ((t.scheduled_start_minutes || 0) / totalSpan) * 100;
                const widthPct = Math.max(4, (t.duration_minutes / totalSpan) * 100);

                return (
                  <div key={t.id} className="space-y-1">
                    <div className="flex justify-between text-[11px] text-slate-400">
                      <span className="font-bold text-slate-300">{t.id}: {t.title}</span>
                      <span>T+{t.scheduled_start_minutes}m to T+{t.scheduled_end_minutes}m</span>
                    </div>
                    <div className="w-full bg-space-900 h-5 rounded overflow-hidden relative">
                      <div
                        className="absolute h-full bg-gradient-to-r from-cyan-600 to-blue-600 rounded flex items-center px-2 text-[10px] text-white font-bold truncate"
                        style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                      >
                        {t.id} ({t.duration_minutes}m)
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Create Task Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-space-800 border border-space-500 rounded-xl p-5 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-space-700 pb-3">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <Plus className="w-4 h-4 text-cyan-400" />
                CREATE MISSION TASK
              </h3>
              <button onClick={() => setIsCreateOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">TASK ID</label>
                  <input
                    required
                    type="text"
                    value={newId}
                    onChange={(e) => setNewId(e.target.value)}
                    placeholder="TSK-01"
                    className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">PRIORITY (1=Crit, 4=Low)</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(Number(e.target.value))}
                    className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                  >
                    <option value={1}>1 - Critical</option>
                    <option value={2}>2 - High</option>
                    <option value={3}>3 - Medium</option>
                    <option value={4}>4 - Low</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">TASK TITLE</label>
                <input
                  required
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Deploy High-Gain Antenna"
                  className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">DESCRIPTION</label>
                <textarea
                  rows={2}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="ADCS pointing lock and antenna gimbal calibration..."
                  className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">DURATION (MIN)</label>
                  <input
                    required
                    type="number"
                    min={1}
                    value={newDuration}
                    onChange={(e) => setNewDuration(Number(e.target.value))}
                    className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">EARLIEST START (M)</label>
                  <input
                    type="number"
                    min={0}
                    value={newEarliestStart}
                    onChange={(e) => setNewEarliestStart(Number(e.target.value))}
                    className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">DEADLINE (M)</label>
                  <input
                    type="number"
                    value={newDeadline}
                    onChange={(e) => setNewDeadline(e.target.value)}
                    placeholder="Optional"
                    className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">DEPENDENCY TASK IDs (Comma-separated)</label>
                <input
                  type="text"
                  value={newDeps}
                  onChange={(e) => setNewDeps(e.target.value)}
                  placeholder="TSK-01, TSK-02"
                  className="w-full bg-space-700 border border-space-500 rounded p-2 text-white"
                />
              </div>

              {formError && (
                <div className="p-2 rounded bg-red-950/40 border border-red-500/40 text-red-300 text-[11px]">
                  {formError}
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-3 py-1.5 rounded bg-space-700 hover:bg-space-600 text-slate-300 border border-space-600"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold"
                >
                  CREATE TASK
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
