import React, { useState, useEffect } from 'react';
import { useAurora } from '../../context/AuroraContext';
import { api } from '../../lib/api-client';
import { ReplayFramesResponse, ReplayFrame } from '../../types';
import {
  ScrollText,
  Filter,
  Search,
  Download,
  PlayCircle,
  Clock,
  RefreshCw,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  Rewind,
  FastForward,
  AlertTriangle,
  CheckCircle2,
  Thermometer,
  BatteryCharging,
  Zap,
  Compass,
  Radio,
  Database,
  Sliders,
  Eye,
} from 'lucide-react';

export const EventLogView: React.FC = () => {
  const { events, simStatus, refreshAll } = useAurora();
  const [filterCategory, setFilterCategory] = useState<string>('ALL');
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Replay scrubber state
  const [replayData, setReplayData] = useState<ReplayFramesResponse | null>(null);
  const [isLoadingReplay, setIsLoadingReplay] = useState<boolean>(false);
  const [isScrubberOpen, setIsScrubberOpen] = useState<boolean>(false);
  const [currentFrameIdx, setCurrentFrameIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1); // 1x, 2x, 5x

  const filteredEvents = events.filter((e) => {
    if (filterCategory !== 'ALL' && e.category !== filterCategory) return false;
    if (filterSeverity !== 'ALL' && e.severity !== filterSeverity) return false;
    if (searchQuery.trim() && !e.message.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  const handleLoadReplayScrubber = async () => {
    if (!simStatus?.run_id) return;
    setIsLoadingReplay(true);
    try {
      const data = await api.getReplayFrames(simStatus.run_id);
      setReplayData(data);
      if (data.frames && data.frames.length > 0) {
        setCurrentFrameIdx(0);
        setIsScrubberOpen(true);
      }
    } catch (err) {
      console.error('Failed to load replay frames:', err);
    } finally {
      setIsLoadingReplay(false);
    }
  };

  // Playback timer loop
  useEffect(() => {
    if (!isPlaying || !replayData || !replayData.frames || replayData.frames.length === 0) return;

    const intervalMs = Math.max(100, Math.floor(1000 / playbackSpeed));
    const timer = window.setInterval(() => {
      setCurrentFrameIdx((prev) => {
        if (prev >= replayData.frames.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isPlaying, replayData, playbackSpeed]);

  const currentFrame: ReplayFrame | null =
    replayData && replayData.frames && replayData.frames.length > 0 && currentFrameIdx >= 0 && currentFrameIdx < replayData.frames.length
      ? replayData.frames[currentFrameIdx]
      : null;

  // Correlated events near the current replay frame's simulation timestamp
  const correlatedEvents = currentFrame
    ? events.filter(
        (e) => Math.abs(e.timestamp_sim - currentFrame.timestamp_sim) <= 2.0
      )
    : [];

  const handleExportCsv = () => {
    window.open('/api/v1/events/export/csv', '_blank');
  };

  const getModeBadgeClass = (mode: string) => {
    switch (mode) {
      case 'NOMINAL':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
      case 'SAFE_MODE':
        return 'bg-red-500/20 text-red-400 border-red-500/40 animate-pulse';
      case 'DEGRADED':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'RECOVERY':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/40';
      case 'STANDBY':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/40';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/40';
    }
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3 font-mono text-xs">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <ScrollText className="w-4 h-4 text-cyan-400" />
            MISSION EVENT LOG & REPLAY
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Immutable chronological audit log and non-mutating historical frame playback scrubber.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleLoadReplayScrubber}
            disabled={isLoadingReplay || !simStatus?.run_id}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border transition disabled:opacity-50 ${
              isScrubberOpen
                ? 'bg-purple-600/40 text-purple-200 border-purple-400 shadow-[0_0_12px_rgba(168,85,247,0.3)]'
                : 'bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border-purple-500/40'
            }`}
          >
            <PlayCircle className="w-3.5 h-3.5" />
            <span>
              {isLoadingReplay
                ? 'LOADING BLACK BOX...'
                : isScrubberOpen
                ? 'REPLAY SCRUBBER ACTIVE'
                : 'OPEN MISSION REPLAY SCRUBBER'}
            </span>
          </button>
          <button
            onClick={handleExportCsv}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>EXPORT CSV</span>
          </button>
        </div>
      </div>

      {/* Interactive Mission Replay Scrubber Deck */}
      {isScrubberOpen && replayData && replayData.frames && (
        <div className="bg-space-800 border-2 border-purple-500/50 rounded-xl p-5 space-y-4 font-mono text-xs shadow-2xl relative">
          {/* Read-Only Safety Banner */}
          <div className="flex items-center justify-between bg-purple-950/70 border border-purple-500/50 rounded-lg px-4 py-2 text-purple-200">
            <div className="flex items-center space-x-2">
              <Eye className="w-4 h-4 text-purple-400 animate-pulse" />
              <span className="font-bold tracking-wider text-[11px]">
                HISTORICAL MISSION REPLAY MODE — READ ONLY (DOES NOT MUTATE LIVE SIMULATOR)
              </span>
            </div>
            <button
              onClick={() => {
                setIsScrubberOpen(false);
                setIsPlaying(false);
              }}
              className="text-purple-300 hover:text-white px-2 py-0.5 rounded bg-purple-900/60 hover:bg-purple-800 transition"
            >
              DISMISS DECK
            </button>
          </div>

          {/* Scrubber Timeline Controls */}
          <div className="bg-space-900/90 border border-space-700 rounded-lg p-4 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center space-x-2">
                <span className="text-slate-400">FRAME:</span>
                <span className="text-cyan-300 font-bold text-sm">
                  {replayData.frames.length > 0 ? currentFrameIdx + 1 : 0}
                </span>
                <span className="text-slate-500">/ {replayData.frames.length}</span>
                <span className="text-slate-600">|</span>
                <span className="text-slate-400">TIME:</span>
                <span className="text-amber-300 font-bold text-sm">
                  T+{currentFrame?.timestamp_sim.toFixed(1) ?? '0.0'}s
                </span>
              </div>

              {/* Playback Controls & Speed */}
              <div className="flex items-center space-x-2">
                {/* Jump to Start */}
                <button
                  onClick={() => {
                    setIsPlaying(false);
                    setCurrentFrameIdx(0);
                  }}
                  title="Jump to Start"
                  className="p-1.5 rounded bg-space-800 hover:bg-space-700 text-slate-300 border border-space-600"
                >
                  <SkipBack className="w-4 h-4" />
                </button>

                {/* Step Back */}
                <button
                  onClick={() => {
                    setIsPlaying(false);
                    setCurrentFrameIdx((p) => Math.max(0, p - 1));
                  }}
                  title="Step Backward (1 frame)"
                  className="p-1.5 rounded bg-space-800 hover:bg-space-700 text-slate-300 border border-space-600"
                >
                  <Rewind className="w-4 h-4" />
                </button>

                {/* Play / Pause */}
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className={`flex items-center space-x-1 px-3 py-1.5 rounded font-bold transition ${
                    isPlaying
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50'
                      : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 hover:bg-emerald-500/30'
                  }`}
                >
                  {isPlaying ? (
                    <>
                      <Pause className="w-4 h-4" />
                      <span>PAUSE</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      <span>PLAY</span>
                    </>
                  )}
                </button>

                {/* Step Forward */}
                <button
                  onClick={() => {
                    setIsPlaying(false);
                    setCurrentFrameIdx((p) =>
                      replayData.frames ? Math.min(replayData.frames.length - 1, p + 1) : 0
                    );
                  }}
                  title="Step Forward (1 frame)"
                  className="p-1.5 rounded bg-space-800 hover:bg-space-700 text-slate-300 border border-space-600"
                >
                  <FastForward className="w-4 h-4" />
                </button>

                {/* Jump to End */}
                <button
                  onClick={() => {
                    setIsPlaying(false);
                    if (replayData.frames) {
                      setCurrentFrameIdx(replayData.frames.length - 1);
                    }
                  }}
                  title="Jump to End"
                  className="p-1.5 rounded bg-space-800 hover:bg-space-700 text-slate-300 border border-space-600"
                >
                  <SkipForward className="w-4 h-4" />
                </button>

                {/* Speed Selector */}
                <div className="flex items-center space-x-1 pl-2 border-l border-space-700">
                  <span className="text-slate-500 text-[10px]">SPEED:</span>
                  {[1, 2, 5].map((spd) => (
                    <button
                      key={spd}
                      onClick={() => setPlaybackSpeed(spd)}
                      className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        playbackSpeed === spd
                          ? 'bg-purple-600 text-white'
                          : 'bg-space-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      {spd}x
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Range Slider Scrubber */}
            <div className="pt-2">
              <input
                type="range"
                min={0}
                max={replayData.frames.length > 0 ? replayData.frames.length - 1 : 0}
                value={currentFrameIdx}
                onChange={(e) => {
                  setIsPlaying(false);
                  setCurrentFrameIdx(Number(e.target.value));
                }}
                className="w-full accent-cyan-400 h-2 bg-space-950 rounded-lg cursor-pointer appearance-none border border-space-700"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>START: T+{replayData.min_sim_time.toFixed(1)}s</span>
                <span className="text-purple-300">
                  RECONSTRUCTION RANGE: {(replayData.max_sim_time - replayData.min_sim_time).toFixed(1)}s DURATION
                </span>
                <span>END: T+{replayData.max_sim_time.toFixed(1)}s</span>
              </div>
            </div>
          </div>

          {/* Historical Telemetry Snapshot at Scrubbed Frame */}
          {currentFrame && (
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-space-700 pb-2">
                <span className="text-slate-400 font-bold uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  RECONSTRUCTED TELEMETRY SNAPSHOT (T+{currentFrame.timestamp_sim.toFixed(1)}s)
                </span>
                <div className="flex items-center space-x-2">
                  <span className="text-slate-500 text-[11px]">SPACECRAFT STATE:</span>
                  <span
                    className={`px-2.5 py-0.5 rounded border text-[11px] font-bold ${getModeBadgeClass(
                      currentFrame.mode
                    )}`}
                  >
                    {currentFrame.mode}
                  </span>
                </div>
              </div>

              {/* Subsystems Snapshot Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2.5">
                {/* Thermal */}
                <div
                  className={`p-2.5 rounded-lg border ${
                    currentFrame.temperature_c >= 75.0
                      ? 'bg-red-950/40 border-red-500/60'
                      : 'bg-space-900 border-space-700'
                  }`}
                >
                  <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] mb-1">
                    <Thermometer
                      className={`w-3.5 h-3.5 ${
                        currentFrame.temperature_c >= 75.0 ? 'text-red-400' : 'text-cyan-400'
                      }`}
                    />
                    <span>CORE TEMP</span>
                  </div>
                  <div
                    className={`text-base font-bold ${
                      currentFrame.temperature_c >= 75.0 ? 'text-red-400' : 'text-slate-100'
                    }`}
                  >
                    {currentFrame.temperature_c.toFixed(1)}°C
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">LIMIT: 75.0°C</div>
                </div>

                {/* Battery */}
                <div className="p-2.5 rounded-lg bg-space-900 border border-space-700">
                  <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] mb-1">
                    <BatteryCharging className="w-3.5 h-3.5 text-emerald-400" />
                    <span>BATTERY SOC</span>
                  </div>
                  <div className="text-base font-bold text-slate-100">
                    {currentFrame.battery_soc_pct.toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    {currentFrame.battery_soc_pct < 20.0 ? 'CRITICAL LOW' : 'NOMINAL RANGE'}
                  </div>
                </div>

                {/* Bus Power */}
                <div className="p-2.5 rounded-lg bg-space-900 border border-space-700">
                  <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] mb-1">
                    <Zap className="w-3.5 h-3.5 text-amber-400" />
                    <span>BUS POWER</span>
                  </div>
                  <div className="text-base font-bold text-slate-100">
                    {currentFrame.bus_voltage_v.toFixed(1)} V
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    DRAW: {currentFrame.current_draw_a.toFixed(1)} A
                  </div>
                </div>

                {/* Communications */}
                <div className="p-2.5 rounded-lg bg-space-900 border border-space-700">
                  <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] mb-1">
                    <Radio className="w-3.5 h-3.5 text-cyan-400" />
                    <span>COMMS LINK</span>
                  </div>
                  <div
                    className={`text-base font-bold ${
                      currentFrame.comm_status === 'NOMINAL'
                        ? 'text-emerald-400'
                        : currentFrame.comm_status === 'DEGRADED'
                        ? 'text-amber-400'
                        : 'text-red-400'
                    }`}
                  >
                    {currentFrame.comm_status}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    SIGNAL: {currentFrame.signal_quality_pct.toFixed(0)}%
                  </div>
                </div>

                {/* ADCS */}
                <div className="p-2.5 rounded-lg bg-space-900 border border-space-700">
                  <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] mb-1">
                    <Compass className="w-3.5 h-3.5 text-blue-400" />
                    <span>ADCS ERROR</span>
                  </div>
                  <div className="text-base font-bold text-slate-100">
                    {currentFrame.attitude_error_deg.toFixed(2)}°
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    RATE: {currentFrame.angular_rate_deg_s.toFixed(3)}°/s
                  </div>
                </div>

                {/* OBDH & Health */}
                <div className="p-2.5 rounded-lg bg-space-900 border border-space-700">
                  <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] mb-1">
                    <Database className="w-3.5 h-3.5 text-purple-400" />
                    <span>OBDH STORAGE</span>
                  </div>
                  <div className="text-base font-bold text-slate-100">
                    {currentFrame.storage_used_pct.toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    SENSORS: {currentFrame.sensors_valid ? 'VALID' : 'DEGRADED'}
                  </div>
                </div>
              </div>

              {/* Correlated Events at this Timestamp */}
              {correlatedEvents.length > 0 && (
                <div className="p-3 rounded-lg bg-purple-950/40 border border-purple-500/40 space-y-1.5">
                  <span className="text-[11px] font-bold text-purple-300">
                    CORRELATED AUDIT EVENTS (NEAR T+{currentFrame.timestamp_sim.toFixed(1)}s):
                  </span>
                  <div className="space-y-1 max-h-24 overflow-y-auto">
                    {correlatedEvents.map((evt) => (
                      <div
                        key={evt.id}
                        className="flex items-center justify-between text-[11px] bg-space-900/80 px-2 py-1 rounded border border-space-800"
                      >
                        <div className="flex items-center space-x-2">
                          <span className="text-cyan-400 font-bold">T+{evt.timestamp_sim.toFixed(1)}s</span>
                          <span
                            className={`px-1 py-0.2 rounded text-[9px] font-bold ${
                              evt.severity === 'CRITICAL'
                                ? 'bg-red-500/20 text-red-400'
                                : evt.severity === 'WARNING'
                                ? 'bg-amber-500/20 text-amber-400'
                                : 'bg-cyan-500/20 text-cyan-400'
                            }`}
                          >
                            {evt.severity}
                          </span>
                          <span className="text-slate-200">{evt.message}</span>
                        </div>
                        <span className="text-[10px] text-slate-500">{evt.category}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Event Filters & Table */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3 font-mono text-xs">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-space-700">
          <div className="flex items-center space-x-2 flex-grow max-w-sm">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Filter by keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-space-700 border border-space-500 rounded px-2.5 py-1 text-slate-200 outline-none focus:border-cyan-400 text-xs"
            />
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              <span className="text-slate-400">SEVERITY:</span>
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value)}
                className="bg-space-700 border border-space-500 rounded px-2 py-1 text-slate-200 text-xs"
              >
                <option value="ALL">ALL</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="WARNING">WARNING</option>
                <option value="INFO">INFO</option>
              </select>
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-slate-400">CATEGORY:</span>
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="bg-space-700 border border-space-500 rounded px-2 py-1 text-slate-200 text-xs"
              >
                <option value="ALL">ALL</option>
                <option value="OPERATIONS">OPERATIONS</option>
                <option value="FAULT">FAULT</option>
                <option value="SYSTEM">SYSTEM</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto max-h-[500px]">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-space-700 text-slate-500 text-[11px]">
                <th className="py-2 px-3">EVENT_ID</th>
                <th className="py-2 px-3">SIM_T (s)</th>
                <th className="py-2 px-3">SEVERITY</th>
                <th className="py-2 px-3">CATEGORY</th>
                <th className="py-2 px-3">MESSAGE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-space-700/60 text-slate-300">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500">
                    No matching events found in audit buffer.
                  </td>
                </tr>
              ) : (
                filteredEvents.map((evt) => (
                  <tr key={evt.id} className="hover:bg-space-700/40 transition">
                    <td className="py-2 px-3 font-bold text-cyan-300">{evt.id}</td>
                    <td className="py-2 px-3 text-slate-400">T+{evt.timestamp_sim.toFixed(1)}s</td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          evt.severity === 'CRITICAL'
                            ? 'bg-red-500/20 text-red-400'
                            : evt.severity === 'WARNING'
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-cyan-500/20 text-cyan-400'
                        }`}
                      >
                        {evt.severity}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-400">{evt.category}</td>
                    <td className="py-2 px-3 text-slate-200">{evt.message}</td>
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
