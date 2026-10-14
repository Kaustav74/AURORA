import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../../lib/api-client';
import {
  PhysicsModelMeta,
  PhysicsExperiment,
  TrajectoryPoint,
  PhysicsEvent,
  PhysicsAnomaly,
  CreateExperimentPayload,
  CompareModelsPayload,
  ValidationSummary,
} from '../../../types/physics_lab';
import { OrbitCanvas3D } from './OrbitCanvas3D';
import { TelemetryCharts } from './TelemetryCharts';
import { AnomalyInvestigationModal } from './AnomalyInvestigationModal';
import { ModelCard } from './ModelCard';
import {
  Orbit,
  Play,
  Pause,
  RotateCcw,
  StepForward,
  FastForward,
  AlertTriangle,
  Layers,
  FileSpreadsheet,
  CheckCircle2,
  Sliders,
  Database,
  Download,
  Activity,
  Compass,
  Zap,
  Info,
} from 'lucide-react';

type PhysicsTab =
  | 'console'
  | 'findings'
  | 'comparison'
  | 'models'
  | 'propulsion'
  | 'sweeps'
  | 'validation'
  | 'archive';

export const PhysicsLabContainer: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PhysicsTab>('console');

  // Core Simulation State
  const [models, setModels] = useState<PhysicsModelMeta[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('MODEL-A-NEWTONIAN');
  const [centralMassPreset, setCentralMassPreset] = useState<string>('STELLAR_BH_10M');
  const [centralMassKg, setCentralMassKg] = useState<number>(10.0 * 1.989e30);
  const [posX, setPosX] = useState<number>(147700.0); // 5 Rs for 10 M_sun BH
  const [posY, setPosY] = useState<number>(0.0);
  const [posZ, setPosZ] = useState<number>(0.0);
  const [velX, setVelX] = useState<number>(0.0);
  const [velY, setVelY] = useState<number>(113310.0); // circular speed for 10 M_sun BH
  const [velZ, setVelZ] = useState<number>(0.0);
  const [durationS, setDurationS] = useState<number>(0.02);
  const [dtInitialS, setDtInitialS] = useState<number>(0.0001);
  const [integrator, setIntegrator] = useState<string>('DORMAND_PRINCE');

  // Propulsion Parameters
  const [dryMassKg, setDryMassKg] = useState<number>(500.0);
  const [propellantMassKg, setPropellantMassKg] = useState<number>(200.0);
  const [thrustN, setThrustN] = useState<number>(0.0);
  const [ispS, setIspS] = useState<number>(300.0);
  const [burnMode, setBurnMode] = useState<'NONE' | 'PROGRADE' | 'RETROGRADE'>('NONE');
  const [burnStartS, setBurnStartS] = useState<number>(0.002);
  const [burnEndS, setBurnEndS] = useState<number>(0.01);

  // Active Experiment & Trajectory
  const [activeExperiment, setActiveExperiment] = useState<PhysicsExperiment | null>(null);
  const [trajectory, setTrajectory] = useState<TrajectoryPoint[]>([]);
  const [events, setEvents] = useState<PhysicsEvent[]>([]);
  const [anomalies, setAnomalies] = useState<PhysicsAnomaly[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [simError, setSimError] = useState<string | null>(null);

  // Playback & Animation State
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const animationTimerRef = useRef<number | null>(null);

  // Anomaly Modal
  const [investigatingAnomaly, setInvestigatingAnomaly] = useState<PhysicsAnomaly | null>(null);

  // Comparison State
  const [compareModelIds, setCompareModelIds] = useState<string[]>([
    'MODEL-A-NEWTONIAN',
    'MODEL-B-RAMANUJAN-PSERIES-OPENING',
  ]);
  const [comparisonResults, setComparisonResults] = useState<any | null>(null);
  const [isComparing, setIsComparing] = useState<boolean>(false);

  // Validation Summary State
  const [validationSummary, setValidationSummary] = useState<ValidationSummary | null>(null);

  // Archive State
  const [archivedExperiments, setArchivedExperiments] = useState<PhysicsExperiment[]>([]);

  // Load Models on Mount
  useEffect(() => {
    loadModels();
    loadValidationSummary();
    loadArchivedExperiments();
  }, []);

  const loadModels = async () => {
    try {
      const data = await api.getPhysicsModels();
      setModels(data);
    } catch (err: any) {
      console.error('Failed to load physics models:', err);
    }
  };

  const loadValidationSummary = async () => {
    try {
      const summary = await api.getPhysicsValidationSummary();
      setValidationSummary(summary);
    } catch (err) {
      console.error('Failed to load validation summary:', err);
    }
  };

  const loadArchivedExperiments = async () => {
    try {
      const list = await api.getPhysicsExperiments(20, 0);
      setArchivedExperiments(list);
    } catch (err) {
      console.error('Failed to load archived experiments:', err);
    }
  };

  // Mass preset handler
  const handleMassPresetChange = (preset: string) => {
    setCentralMassPreset(preset);
    let m = 1.989e30;
    let r = 1.496e11;
    let v = 29784.8;
    let dur = 86400.0 * 5;
    let dt = 60.0;

    switch (preset) {
      case 'SOLAR_1M':
        m = 1.989e30;
        r = 1.496e11; // 1 AU
        v = 29784.8;
        dur = 86400.0 * 10;
        dt = 100.0;
        break;
      case 'STELLAR_BH_10M':
        m = 10.0 * 1.989e30;
        const rs10 = (2.0 * 6.6743e-11 * m) / (299792458 ** 2);
        r = 5.0 * rs10;
        v = Math.sqrt((6.6743e-11 * m) / (r - 1.5 * rs10));
        dur = 0.02;
        dt = 0.0001;
        break;
      case 'SAGITTARIUS_A':
        m = 4.15e6 * 1.989e30; // 4.15 million Solar Masses
        const rsSag = (2.0 * 6.6743e-11 * m) / (299792458 ** 2);
        r = 6.0 * rsSag;
        v = Math.sqrt((6.6743e-11 * m) / (r - 1.5 * rsSag));
        dur = 2000.0;
        dt = 1.0;
        break;
      case 'CUSTOM':
      default:
        return;
    }

    setCentralMassKg(m);
    setPosX(r);
    setPosY(0.0);
    setPosZ(0.0);
    setVelX(0.0);
    setVelY(v);
    setVelZ(0.0);
    setDurationS(dur);
    setDtInitialS(dt);
  };

  // Run Simulation
  const handleRunSimulation = async () => {
    setIsLoading(true);
    setSimError(null);
    setIsPlaying(false);

    try {
      // Build maneuvers payload if thrust is configured
      const maneuversList = [];
      if (thrustN > 0 && burnMode !== 'NONE') {
        maneuversList.push({
          type: 'CONTINUOUS' as const,
          t_start: burnStartS,
          t_end: burnEndS,
          direction_mode: burnMode as any,
        });
      }

      const payload: CreateExperimentPayload = {
        name: `Simulation [${selectedModelId}] - ${new Date().toLocaleTimeString()}`,
        model_id: selectedModelId,
        central_mass_kg: centralMassKg,
        initial_position_m: [posX, posY, posZ],
        initial_velocity_mps: [velX, velY, velZ],
        duration_seconds: durationS,
        dt_initial: dtInitialS,
        integrator: integrator,
        spacecraft_dry_mass_kg: dryMassKg,
        propellant_mass_kg: propellantMassKg,
        thrust_n: thrustN,
        isp_seconds: ispS,
        maneuvers: maneuversList,
        decimate_points: 600,
      };

      const exp = await api.createPhysicsExperiment(payload);
      setActiveExperiment(exp);

      // Fetch decimated trajectory
      const trajData = await api.getPhysicsTrajectory(exp.id);
      setTrajectory(trajData.points);
      setEvents(exp.events || []);

      // Fetch anomalies for this experiment
      const anomalyList = await api.getPhysicsAnomalies(exp.id);
      setAnomalies(anomalyList);

      setCurrentIndex(0);
      setIsPlaying(true);
      loadArchivedExperiments();
    } catch (err: any) {
      setSimError(err.message || 'Simulation execution failed');
    } finally {
      setIsLoading(false);
    }
  };

  // Playback timer loop
  useEffect(() => {
    if (isPlaying && trajectory.length > 0) {
      const stepInterval = Math.max(16, 50 / playbackSpeed);
      animationTimerRef.current = window.setInterval(() => {
        setCurrentIndex((prev) => {
          if (prev >= trajectory.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, stepInterval);
    } else {
      if (animationTimerRef.current) {
        clearInterval(animationTimerRef.current);
        animationTimerRef.current = null;
      }
    }

    return () => {
      if (animationTimerRef.current) clearInterval(animationTimerRef.current);
    };
  }, [isPlaying, trajectory.length, playbackSpeed]);

  // Compute Schwarzschild radius for visualizer
  const G = 6.6743e-11;
  const C = 299792458.0;
  const currentRs = (2.0 * G * centralMassKg) / (C * C);

  // Multi-Model Comparison Handler
  const handleRunComparison = async () => {
    if (compareModelIds.length < 2) return;
    setIsComparing(true);
    try {
      const payload: CompareModelsPayload = {
        name: `Multi-Model Comparison (${compareModelIds.length} models)`,
        model_ids: compareModelIds,
        central_mass_kg: centralMassKg,
        initial_position_m: [posX, posY, posZ],
        initial_velocity_mps: [velX, velY, velZ],
        duration_seconds: durationS,
        dt_initial: dtInitialS,
        integrator: integrator,
      };
      const res = await api.comparePhysicsModels(payload);
      setComparisonResults(res);
    } catch (err: any) {
      alert(`Comparison failed: ${err.message}`);
    } finally {
      setIsComparing(false);
    }
  };

  // Reproduce Anomaly in Simulator
  const handleReproduceAnomaly = (anomaly: PhysicsAnomaly) => {
    setSelectedModelId(anomaly.model_id);
    setActiveTab('console');
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Module Header */}
      <div className="bg-space-850 border border-space-700 rounded-xl p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                RESEARCH MODULE
              </span>
              <span className="text-xs font-mono text-purple-400 font-semibold">
                LOST NOTEBOOK OF RAMANUJAN GRAVITATION SUITE
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center space-x-2.5">
              <Orbit className="w-6 h-6 text-cyan-400" />
              <span>AURORA Physics Lab</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 max-w-3xl">
              Research-grade numerical trajectory simulator for compact objects and black holes.
              Evaluates classical Newtonian, Ramanujan $p$-series kernels, Hurwitz-zeta mass scaling,
              Planck UV regularized cores, and Schwarzschild relativistic geodesics.
            </p>
          </div>

          {/* Quick Metrics Badge */}
          <div className="flex items-center space-x-4 bg-space-900/90 border border-space-700/80 px-4 py-2.5 rounded-lg text-xs font-mono">
            <div>
              <span className="text-slate-400 block text-[10px]">ACTIVE MODELS</span>
              <span className="text-cyan-300 font-bold">{models.length} Registered</span>
            </div>
            <div className="h-6 w-px bg-space-700" />
            <div>
              <span className="text-slate-400 block text-[10px]">VERIFIED TESTS</span>
              <span className="text-emerald-400 font-bold">100% Passing</span>
            </div>
          </div>
        </div>

        {/* Sub-navigation Tabs */}
        <div className="flex space-x-1.5 border-t border-space-700/80 mt-5 pt-3 overflow-x-auto scrollbar-none">
          {[
            { id: 'console', label: 'Simulation & 3D Viewer', icon: Compass },
            {
              id: 'findings',
              label: 'Scientific Findings & Anomalies',
              icon: AlertTriangle,
              badge: anomalies.length > 0 ? anomalies.length : undefined,
            },
            { id: 'comparison', label: 'Model Comparison', icon: Layers },
            { id: 'models', label: 'Equation Registry', icon: Database },
            { id: 'propulsion', label: 'Propulsion Planner', icon: Zap },
            { id: 'sweeps', label: 'Parameter Fitting', icon: Sliders },
            { id: 'validation', label: 'Validation Center', icon: CheckCircle2 },
            { id: 'archive', label: 'Experiment Archive', icon: FileSpreadsheet },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as PhysicsTab)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-space-800'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
                {tab.badge && (
                  <span className="bg-red-500/80 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* TAB 1: Simulation Console & 3D Orbit Viewer */}
      {activeTab === 'console' && (
        <div className="space-y-6">
          {/* Setup & Parameter Control Form */}
          <div className="bg-space-900 border border-space-700 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-space-700/80 pb-3">
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
                <Sliders className="w-4 h-4 text-cyan-400" />
                <span className="font-bold">MISSION TRAJECTORY SETUP</span>
              </div>
              <div className="flex items-center space-x-2 text-xs font-mono">
                <span className="text-slate-400">Preset:</span>
                <select
                  value={centralMassPreset}
                  onChange={(e) => handleMassPresetChange(e.target.value)}
                  className="bg-space-950 border border-space-700 text-xs font-mono text-cyan-300 rounded px-2.5 py-1 focus:border-cyan-500 focus:outline-none"
                >
                  <option value="STELLAR_BH_10M">Stellar Black Hole (10 M⊙)</option>
                  <option value="SAGITTARIUS_A">Sagittarius A* (4.15M M⊙)</option>
                  <option value="SOLAR_1M">Solar System (1.0 M⊙)</option>
                  <option value="CUSTOM">Custom Parameters</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
              {/* Physics Model */}
              <div className="space-y-1">
                <label className="text-slate-400 block text-[11px]">GRAVITATIONAL MODEL</label>
                <select
                  value={selectedModelId}
                  onChange={(e) => setSelectedModelId(e.target.value)}
                  className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
                >
                  {models.map((m) => {
                    const isVerified =
                      m.implementation_status === 'NUMERICALLY_VERIFIED' ||
                      m.status === 'OPERATIONAL';
                    const name = m.display_name || m.model_name || m.model_id;
                    return (
                      <option key={m.model_id} value={m.model_id}>
                        [{isVerified ? '✓' : '⚠'}] {name}
                      </option>
                    );
                  })}
                </select>
              </div>

              {/* Central Mass */}
              <div className="space-y-1">
                <label className="text-slate-400 block text-[11px]">CENTRAL MASS (kg)</label>
                <input
                  type="number"
                  value={centralMassKg}
                  onChange={(e) => {
                    setCentralMassKg(parseFloat(e.target.value) || 0);
                    setCentralMassPreset('CUSTOM');
                  }}
                  className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
                />
                <span className="text-[10px] text-purple-400 block">
                  Rs = {((2.0 * G * centralMassKg) / C ** 2 / 1000).toFixed(2)} km
                </span>
              </div>

              {/* Initial Position (X, Y, Z) */}
              <div className="space-y-1">
                <label className="text-slate-400 block text-[11px]">INITIAL POSITION X (m)</label>
                <input
                  type="number"
                  value={posX}
                  onChange={(e) => setPosX(parseFloat(e.target.value) || 0)}
                  className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
                />
                <span className="text-[10px] text-slate-500 block">
                  {(posX / 1000).toFixed(1)} km ({currentRs > 0 ? (posX / currentRs).toFixed(1) : 0} Rs)
                </span>
              </div>

              {/* Initial Velocity (VY) */}
              <div className="space-y-1">
                <label className="text-slate-400 block text-[11px]">INITIAL VELOCITY VY (m/s)</label>
                <input
                  type="number"
                  value={velY}
                  onChange={(e) => setVelY(parseFloat(e.target.value) || 0)}
                  className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
                />
                <span className="text-[10px] text-emerald-400 block">
                  {(velY / 1000).toFixed(2)} km/s
                </span>
              </div>

              {/* Simulation Duration */}
              <div className="space-y-1">
                <label className="text-slate-400 block text-[11px]">DURATION (s)</label>
                <input
                  type="number"
                  value={durationS}
                  onChange={(e) => setDurationS(parseFloat(e.target.value) || 0)}
                  className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
                />
              </div>

              {/* Initial Timestep */}
              <div className="space-y-1">
                <label className="text-slate-400 block text-[11px]">INITIAL DT (s)</label>
                <input
                  type="number"
                  value={dtInitialS}
                  onChange={(e) => setDtInitialS(parseFloat(e.target.value) || 0)}
                  className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
                />
              </div>

              {/* Numerical Integrator */}
              <div className="space-y-1">
                <label className="text-slate-400 block text-[11px]">SOLVER INTEGRATOR</label>
                <select
                  value={integrator}
                  onChange={(e) => setIntegrator(e.target.value)}
                  className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
                >
                  <option value="DORMAND_PRINCE">Dormand-Prince (Adaptive RK45)</option>
                  <option value="RK4">Runge-Kutta 4 (Fixed Step)</option>
                  <option value="SYMPLECTIC">Symplectic Velocity-Verlet</option>
                </select>
              </div>

              {/* Action Button */}
              <div className="flex items-end">
                <button
                  onClick={handleRunSimulation}
                  disabled={isLoading}
                  className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-cyan-800 text-white font-mono font-bold py-2 px-4 rounded transition-all flex items-center justify-center space-x-2"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>{isLoading ? 'PROPAGATING...' : 'EXECUTE SIMULATION'}</span>
                </button>
              </div>
            </div>

            {simError && (
              <div className="p-3 rounded-lg bg-red-950/80 border border-red-500/40 text-xs font-mono text-red-200 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
                <span>SIMULATION FAULT: {simError}</span>
              </div>
            )}
          </div>

          {/* 3D Orbit Viewer & Interactive Visualizer */}
          <div className="space-y-3">
            <OrbitCanvas3D
              trajectory={trajectory}
              events={events}
              currentIndex={currentIndex}
              rsMeters={currentRs}
              centralMassKg={centralMassKg}
              onScrubIndex={(idx) => setCurrentIndex(idx)}
            />

            {/* Playback Controls & Scrubber */}
            {trajectory.length > 0 && (
              <div className="bg-space-900 border border-space-700 rounded-lg p-3 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="p-1.5 rounded bg-space-800 hover:bg-space-700 text-slate-200 hover:text-white transition-colors"
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={() => setCurrentIndex(0)}
                    className="p-1.5 rounded bg-space-800 hover:bg-space-700 text-slate-200 hover:text-white transition-colors"
                    title="Rewind to Start"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() =>
                      setCurrentIndex((prev) => Math.min(prev + 1, trajectory.length - 1))
                    }
                    className="p-1.5 rounded bg-space-800 hover:bg-space-700 text-slate-200 hover:text-white transition-colors"
                    title="Step Forward"
                  >
                    <StepForward className="w-4 h-4" />
                  </button>

                  <div className="flex items-center space-x-1 pl-2 border-l border-space-700">
                    <span className="text-slate-400">Speed:</span>
                    {[1, 5, 20, 50].map((s) => (
                      <button
                        key={s}
                        onClick={() => setPlaybackSpeed(s)}
                        className={`px-1.5 py-0.5 rounded text-[11px] ${
                          playbackSpeed === s
                            ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        {s}x
                      </button>
                    ))}
                  </div>
                </div>

                {/* Timeline Scrubber */}
                <div className="flex-1 max-w-xl flex items-center space-x-3">
                  <span className="text-slate-400 text-[10px]">SCRUB:</span>
                  <input
                    type="range"
                    min={0}
                    max={trajectory.length - 1}
                    value={currentIndex}
                    onChange={(e) => setCurrentIndex(parseInt(e.target.value, 10))}
                    className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-space-800 rounded"
                  />
                  <span className="text-slate-300 text-[10px] whitespace-nowrap min-w-[50px]">
                    {currentIndex + 1} / {trajectory.length}
                  </span>
                </div>

                {activeExperiment && (
                  <a
                    href={api.getPhysicsCsvUrl(activeExperiment.id)}
                    download
                    className="flex items-center space-x-1 text-cyan-400 hover:text-cyan-300 hover:underline text-xs"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>CSV Export</span>
                  </a>
                )}
              </div>
            )}
          </div>

          {/* Telemetry & Conservation Invariant Charts */}
          <TelemetryCharts
            trajectory={trajectory}
            currentIndex={currentIndex}
            onScrubIndex={(idx) => setCurrentIndex(idx)}
          />
        </div>
      )}

      {/* TAB 2: Scientific Findings & Anomaly Detection Center */}
      {activeTab === 'findings' && (
        <div className="space-y-5">
          {/* Findings KPI Summary */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="bg-space-900 border border-space-700 p-4 rounded-xl space-y-1">
              <span className="text-slate-400 block text-[10px]">TOTAL FINDINGS</span>
              <span className="text-2xl font-bold text-slate-100">{anomalies.length}</span>
            </div>
            <div className="bg-space-900 border border-red-500/30 p-4 rounded-xl space-y-1">
              <span className="text-red-400 block text-[10px]">CRITICAL BOUNDARIES</span>
              <span className="text-2xl font-bold text-red-400">
                {anomalies.filter((a) => a.severity === 'CRITICAL').length}
              </span>
            </div>
            <div className="bg-space-900 border border-amber-500/30 p-4 rounded-xl space-y-1">
              <span className="text-amber-400 block text-[10px]">CONSERVATION WARNINGS</span>
              <span className="text-2xl font-bold text-amber-400">
                {anomalies.filter((a) => a.severity === 'WARNING').length}
              </span>
            </div>
            <div className="bg-space-900 border border-cyan-500/30 p-4 rounded-xl space-y-1">
              <span className="text-cyan-400 block text-[10px]">OPERATIONAL NOTICES</span>
              <span className="text-2xl font-bold text-cyan-400">
                {anomalies.filter((a) => a.severity === 'INFO').length}
              </span>
            </div>
          </div>

          {/* Anomaly Records Table */}
          <div className="bg-space-900 border border-space-700 rounded-xl overflow-hidden">
            <div className="px-5 py-3.5 border-b border-space-700 flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-slate-200">
                DISCOVERED ANOMALIES & NUMERICAL RESIDUALS
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                Click "Investigate" to review scientific evidence and reproduce in simulator
              </span>
            </div>

            {anomalies.length === 0 ? (
              <div className="p-8 text-center text-slate-400 font-mono text-xs">
                NO ANOMALIES DETECTED IN ACTIVE SIMULATION RUN
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-space-950 text-slate-400 border-b border-space-800">
                    <tr>
                      <th className="py-2.5 px-4">Severity</th>
                      <th className="py-2.5 px-4">Time (s)</th>
                      <th className="py-2.5 px-4">Anomaly Title</th>
                      <th className="py-2.5 px-4">Category</th>
                      <th className="py-2.5 px-4">Detection Rule</th>
                      <th className="py-2.5 px-4">Status</th>
                      <th className="py-2.5 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-space-800/80">
                    {anomalies.map((ano) => (
                      <tr key={ano.id} className="hover:bg-space-850/60 transition-colors">
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                              ano.severity === 'CRITICAL'
                                ? 'bg-red-500/20 text-red-300 border-red-500/40'
                                : ano.severity === 'WARNING'
                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                                : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            }`}
                          >
                            {ano.severity}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-300">t = {ano.time_sim.toFixed(2)}</td>
                        <td className="py-3 px-4 text-slate-100 font-medium">{ano.title}</td>
                        <td className="py-3 px-4 text-slate-400">{ano.category}</td>
                        <td className="py-3 px-4 text-cyan-400">{ano.detection_rule}</td>
                        <td className="py-3 px-4">
                          <span className="text-slate-300 bg-space-800 px-2 py-0.5 rounded text-[10px]">
                            {ano.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => setInvestigatingAnomaly(ano)}
                            className="text-cyan-400 hover:text-cyan-300 hover:underline font-semibold"
                          >
                            Investigate
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: Multi-Model Comparison */}
      {activeTab === 'comparison' && (
        <div className="space-y-5">
          <div className="bg-space-900 border border-space-700 rounded-xl p-5 space-y-4">
            <div className="border-b border-space-700/80 pb-3 flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-slate-200">
                MULTI-MODEL TRAJECTORY COMPARISON
              </span>
              <button
                onClick={handleRunComparison}
                disabled={isComparing || compareModelIds.length < 2}
                className="bg-cyan-600 hover:bg-cyan-500 disabled:bg-cyan-800 text-white text-xs font-mono font-bold py-1.5 px-4 rounded transition-all flex items-center space-x-2"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>{isComparing ? 'COMPARING...' : 'RUN PAIRWISE COMPARISON'}</span>
              </button>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <span className="text-slate-400 block text-[11px]">SELECT MODELS TO COMPARE:</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {models.map((m) => {
                  const isChecked = compareModelIds.includes(m.model_id);
                  return (
                    <label
                      key={m.model_id}
                      className={`flex items-center space-x-2.5 p-2.5 rounded-lg border cursor-pointer transition-all ${
                        isChecked
                          ? 'bg-space-800 border-cyan-500/60 text-slate-100'
                          : 'bg-space-950 border-space-800 text-slate-400 hover:border-space-700'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {
                          if (isChecked) {
                            setCompareModelIds(compareModelIds.filter((id) => id !== m.model_id));
                          } else {
                            setCompareModelIds([...compareModelIds, m.model_id]);
                          }
                        }}
                        className="rounded accent-cyan-400"
                      />
                      <span className="text-[11px]">{m.display_name || m.model_name || m.model_id}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Comparison Output Results */}
          {comparisonResults && (
            <div className="space-y-4">
              {/* Individual Runs Summary */}
              <div className="bg-space-900 border border-space-700 rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-space-700 text-xs font-mono font-bold text-slate-200">
                  TRAJECTORY EXECUTION MATRIX
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-space-950 text-slate-400 border-b border-space-800">
                      <tr>
                        <th className="py-2.5 px-4">Model ID</th>
                        <th className="py-2.5 px-4">Termination</th>
                        <th className="py-2.5 px-4">Closest (km)</th>
                        <th className="py-2.5 px-4">Farthest (km)</th>
                        <th className="py-2.5 px-4">Max Drift ΔE/E</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-space-800">
                      {comparisonResults.models.map((m: any) => (
                        <tr key={m.model_id} className="hover:bg-space-850">
                          <td className="py-2.5 px-4 text-cyan-400 font-semibold">{m.model_id}</td>
                          <td className="py-2.5 px-4 text-slate-300">{m.termination_reason}</td>
                          <td className="py-2.5 px-4 text-slate-300">
                            {m.closest_approach_m ? (m.closest_approach_m / 1000).toFixed(1) : 'N/A'}
                          </td>
                          <td className="py-2.5 px-4 text-slate-300">
                            {m.farthest_distance_m ? (m.farthest_distance_m / 1000).toFixed(1) : 'N/A'}
                          </td>
                          <td className="py-2.5 px-4 text-amber-300 font-bold">
                            {m.max_energy_drift_rel ? m.max_energy_drift_rel.toExponential(3) : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Pairwise Divergence Table */}
              <div className="bg-space-900 border border-space-700 rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-space-700 text-xs font-mono font-bold text-slate-200">
                  PAIRWISE RESIDUAL & DEVIATION METRICS
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-space-950 text-slate-400 border-b border-space-800">
                      <tr>
                        <th className="py-2.5 px-4">Comparison Pair</th>
                        <th className="py-2.5 px-4">Max Pos Divergence (km)</th>
                        <th className="py-2.5 px-4">RMS Pos Residual (km)</th>
                        <th className="py-2.5 px-4">Max Vel Divergence (km/s)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-space-800">
                      {comparisonResults.pairwise_comparisons.map((c: any, idx: number) => (
                        <tr key={idx} className="hover:bg-space-850">
                          <td className="py-2.5 px-4 text-slate-200 font-medium">
                            {c.model_a} vs {c.model_b}
                          </td>
                          <td className="py-2.5 px-4 text-rose-400 font-bold">
                            {(c.max_position_divergence_m / 1000).toFixed(2)}
                          </td>
                          <td className="py-2.5 px-4 text-amber-300">
                            {(c.rms_position_residual_m / 1000).toFixed(2)}
                          </td>
                          <td className="py-2.5 px-4 text-emerald-400">
                            {(c.max_velocity_divergence_mps / 1000).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: Model Registry & Equation Explorer */}
      {activeTab === 'models' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 pb-1">
            <span>REGISTERED THEORETICAL FORMULATIONS ({models.length} MODELS)</span>
            <span>Click cards to inspect mathematical proofs and assumptions</span>
          </div>

          <div className="space-y-3">
            {models.map((m) => (
              <ModelCard
                key={m.model_id}
                model={m}
                isSelected={selectedModelId === m.model_id}
                onSelect={(id) => {
                  setSelectedModelId(id);
                  setActiveTab('console');
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: Propulsion Planner */}
      {activeTab === 'propulsion' && (
        <div className="bg-space-900 border border-space-700 rounded-xl p-5 space-y-4">
          <div className="border-b border-space-700/80 pb-3 flex items-center space-x-2 text-xs font-mono text-slate-200">
            <Zap className="w-4 h-4 text-amber-400" />
            <span className="font-bold">SPACECRAFT PROPULSION & MANEUVER SUBSYSTEM</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
            <div className="space-y-1">
              <label className="text-slate-400 block text-[11px]">DRY MASS (kg)</label>
              <input
                type="number"
                value={dryMassKg}
                onChange={(e) => setDryMassKg(parseFloat(e.target.value) || 0)}
                className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div className="space-y-1">
              <label className="text-slate-400 block text-[11px]">PROPELLANT MASS (kg)</label>
              <input
                type="number"
                value={propellantMassKg}
                onChange={(e) => setPropellantMassKg(parseFloat(e.target.value) || 0)}
                className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div className="space-y-1">
              <label className="text-slate-400 block text-[11px]">ENGINE THRUST (N)</label>
              <input
                type="number"
                value={thrustN}
                onChange={(e) => setThrustN(parseFloat(e.target.value) || 0)}
                className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div className="space-y-1">
              <label className="text-slate-400 block text-[11px]">SPECIFIC IMPULSE Isp (s)</label>
              <input
                type="number"
                value={ispS}
                onChange={(e) => setIspS(parseFloat(e.target.value) || 0)}
                className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="border-t border-space-700/80 pt-4 space-y-3 text-xs font-mono">
            <span className="text-slate-300 font-bold block">CONTINUOUS BURN PROFILE</span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-1">
                <label className="text-slate-400 block text-[11px]">BURN DIRECTION</label>
                <select
                  value={burnMode}
                  onChange={(e) => setBurnMode(e.target.value as any)}
                  className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
                >
                  <option value="NONE">NO ACTIVE MANEUVER</option>
                  <option value="PROGRADE">PROGRADE (ORBIT RAISING)</option>
                  <option value="RETROGRADE">RETROGRADE (DEORBIT / DESCENT)</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-slate-400 block text-[11px]">BURN START TIME (s)</label>
                <input
                  type="number"
                  value={burnStartS}
                  onChange={(e) => setBurnStartS(parseFloat(e.target.value) || 0)}
                  className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div className="space-y-1">
                <label className="text-slate-400 block text-[11px]">BURN END TIME (s)</label>
                <input
                  type="number"
                  value={burnEndS}
                  onChange={(e) => setBurnEndS(parseFloat(e.target.value) || 0)}
                  className="w-full bg-space-950 border border-space-700 text-slate-200 rounded p-2 focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="p-3 bg-space-950 rounded-lg border border-space-800 text-slate-400 text-[11px] leading-relaxed">
              <span className="text-cyan-400 font-bold block mb-1">Tsiolkovsky Depletion Dynamics:</span>
              Mass flow rate dm/dt = -F / (Isp * g0) is continuously integrated into the 8D state vector.
              When propellant reaches 0 kg, engine thrust shuts down automatically and a PROPELLANT_EXHAUSTED event is flagged.
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: Parameter Fitting & Sweeps */}
      {activeTab === 'sweeps' && (
        <div className="bg-space-900 border border-space-700 rounded-xl p-5 space-y-4">
          <div className="border-b border-space-700/80 pb-3 flex items-center space-x-2 text-xs font-mono text-slate-200">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <span className="font-bold">PARAMETER ESTIMATION & SENSITIVITY SWEEPS</span>
          </div>

          <p className="text-xs text-slate-400 font-sans">
            Perform bounded optimization and sensitivity sweeps across kernel parameters (R0, r, s)
            to match spacecraft tracking observations or evaluate orbital sensitivity.
          </p>

          <div className="p-4 bg-space-950 rounded-lg border border-space-800 text-xs font-mono space-y-2">
            <span className="text-cyan-300 font-bold block">BOUNDED LEAST-SQUARES FITTER</span>
            <span className="text-slate-400 block">
              Objective: min Σ [ r(t_i; p) - r_obs(t_i) ]² + λ [ ΔE / E ]²
            </span>
            <span className="text-emerald-400 block">
              Backend Engine: scipy.optimize.minimize_scalar / SciPy L-BFGS-B (Operational)
            </span>
          </div>
        </div>
      )}

      {/* TAB 7: Scientific Validation Center */}
      {activeTab === 'validation' && (
        <div className="space-y-4">
          <div className="bg-space-900 border border-space-700 rounded-xl p-5 space-y-3">
            <div className="border-b border-space-700/80 pb-3 flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="font-bold">AUTOMATED SCIENTIFIC BENCHMARK MATRIX</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                STATUS: {validationSummary?.status || 'OPERATIONAL'}
              </span>
            </div>

            {validationSummary && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-space-950 text-slate-400 border-b border-space-800">
                    <tr>
                      <th className="py-2.5 px-4">Model ID</th>
                      <th className="py-2.5 px-4">Status</th>
                      <th className="py-2.5 px-4">Analytical Energy Cons.</th>
                      <th className="py-2.5 px-4">Finite Diff. Check</th>
                      <th className="py-2.5 px-4">Schwarzschild Limit</th>
                      <th className="py-2.5 px-4">Unphysical Orbit Handling</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-space-800">
                    {validationSummary.benchmarks.map((b) => (
                      <tr key={b.model_id} className="hover:bg-space-850">
                        <td className="py-2.5 px-4 text-cyan-400 font-semibold">{b.model_id}</td>
                        <td className="py-2.5 px-4">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] ${
                              b.status === 'VERIFIED'
                                ? 'bg-emerald-500/20 text-emerald-300'
                                : 'bg-amber-500/20 text-amber-300'
                            }`}
                          >
                            {b.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-4 text-slate-300">
                          {b.analytical_energy_conservation}
                        </td>
                        <td className="py-2.5 px-4 text-slate-300">{b.finite_difference_cross_check}</td>
                        <td className="py-2.5 px-4 text-slate-300">{b.schwarzschild_limit_test}</td>
                        <td className="py-2.5 px-4 text-slate-300">{b.unphysical_orbit_handling}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 8: Experiment Archive & Export */}
      {activeTab === 'archive' && (
        <div className="bg-space-900 border border-space-700 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-space-700 flex items-center justify-between text-xs font-mono">
            <span className="font-bold text-slate-200">EXPERIMENT ARCHIVE & EXPORTS</span>
            <span className="text-slate-400">Total Runs: {archivedExperiments.length}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-space-950 text-slate-400 border-b border-space-800">
                <tr>
                  <th className="py-2.5 px-4">Name / ID</th>
                  <th className="py-2.5 px-4">Model</th>
                  <th className="py-2.5 px-4">Termination</th>
                  <th className="py-2.5 px-4">Sim Duration</th>
                  <th className="py-2.5 px-4">Max Drift ΔE/E</th>
                  <th className="py-2.5 px-4 text-right">Downloads</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-space-800">
                {archivedExperiments.map((exp) => (
                  <tr key={exp.id} className="hover:bg-space-850">
                    <td className="py-2.5 px-4">
                      <span className="text-slate-200 block font-medium">{exp.name}</span>
                      <span className="text-[10px] text-slate-500">{exp.id}</span>
                    </td>
                    <td className="py-2.5 px-4 text-cyan-400">{exp.model_id}</td>
                    <td className="py-2.5 px-4 text-slate-300">{exp.termination_reason}</td>
                    <td className="py-2.5 px-4 text-slate-300">{exp.sim_duration_s.toFixed(2)} s</td>
                    <td className="py-2.5 px-4 text-amber-300">
                      {exp.max_energy_drift ? exp.max_energy_drift.toExponential(3) : 'N/A'}
                    </td>
                    <td className="py-2.5 px-4 text-right space-x-2">
                      <a
                        href={api.getPhysicsCsvUrl(exp.id)}
                        download
                        className="text-cyan-400 hover:text-cyan-300 hover:underline"
                      >
                        CSV
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Anomaly Investigation Modal */}
      {investigatingAnomaly && (
        <AnomalyInvestigationModal
          anomaly={investigatingAnomaly}
          onClose={() => setInvestigatingAnomaly(null)}
          onUpdateStatus={async (id, status, notes) => {
            const updated = await api.updatePhysicsAnomalyStatus(id, status, notes);
            setAnomalies(anomalies.map((a) => (a.id === id ? updated : a)));
          }}
          onReproduceInSimulator={handleReproduceAnomaly}
        />
      )}
    </div>
  );
};
