import React, { useState } from 'react';
import { useAurora } from '../../context/AuroraContext';
import { api } from '../../lib/api-client';
import {
  Download,
  Filter,
  RefreshCw,
  Sliders,
  Database,
  Radio,
  Thermometer,
  Zap,
  Compass,
} from 'lucide-react';
import { TelemetryFrame } from '../../types';

export const TelemetryOperations: React.FC = () => {
  const { telemetry, simStatus, isStale } = useAurora();
  const [historyLimit, setHistoryLimit] = useState<number>(50);
  const [historicalData, setHistoricalData] = useState<TelemetryFrame[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);
  const [filterMode, setFilterMode] = useState<string>('ALL');

  const fetchHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const data = await api.getTelemetryHistory(historyLimit);
      setHistoricalData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleExportCsv = () => {
    window.open('/api/v1/telemetry/export/csv', '_blank');
  };

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-space-800 border border-space-600 rounded-xl p-4">
        <div>
          <h2 className="text-base font-bold text-white font-mono flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            TELEMETRY OPERATIONS & CHANNELS
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Real-time housekeeping telemetry frames, sensor parity checks and historical extraction.
          </p>
        </div>

        <div className="flex items-center space-x-2 font-mono text-xs">
          <button
            onClick={handleExportCsv}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>EXPORT CSV</span>
          </button>
        </div>
      </div>

      {/* Subsystem Telemetry Breakdowns */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Thermal Bay */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-space-700 pb-2">
            <span className="font-bold text-slate-200 flex items-center gap-1.5">
              <Thermometer className="w-4 h-4 text-red-400" />
              THERMAL SUBSYSTEM
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
              telemetry && telemetry.temperature_c >= 75.0 ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'
            }`}>
              {telemetry && telemetry.temperature_c >= 75.0 ? 'OVERHEATING' : 'NOMINAL'}
            </span>
          </div>
          <div className="space-y-1.5 text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Avionics Core Temp:</span>
              <span className="font-bold text-white">{telemetry?.temperature_c.toFixed(2) ?? '--'} °C</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Autonomous Safe Threshold:</span>
              <span className="text-red-400 font-semibold">75.00 °C</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Sunlight Illumination:</span>
              <span>{telemetry?.metadata?.sunlight_factor ? `${(telemetry.metadata.sunlight_factor * 100).toFixed(0)}%` : 'Active'}</span>
            </div>
          </div>
        </div>

        {/* Electrical Power Subsystem */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-space-700 pb-2">
            <span className="font-bold text-slate-200 flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-emerald-400" />
              ELECTRICAL POWER (EPS)
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-400">
              NOMINAL
            </span>
          </div>
          <div className="space-y-1.5 text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Battery State of Charge:</span>
              <span className="font-bold text-white">{telemetry?.battery_soc_pct.toFixed(2) ?? '--'} %</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Main Bus Voltage:</span>
              <span className="font-bold text-white">{telemetry?.bus_voltage_v.toFixed(2) ?? '--'} V</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Total System Current:</span>
              <span className="font-bold text-white">{telemetry?.current_draw_a.toFixed(2) ?? '--'} A</span>
            </div>
          </div>
        </div>

        {/* Communications Subsystem */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-space-700 pb-2">
            <span className="font-bold text-slate-200 flex items-center gap-1.5">
              <Radio className="w-4 h-4 text-cyan-400" />
              COMMUNICATIONS (TTC)
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
              telemetry?.comm_status === 'LOST' ? 'bg-red-500/20 text-red-400' : 'bg-cyan-500/20 text-cyan-400'
            }`}>
              {telemetry?.comm_status || 'NOMINAL'}
            </span>
          </div>
          <div className="space-y-1.5 text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Link Status:</span>
              <span className="font-bold text-white">{telemetry?.comm_status ?? '--'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">RF Signal Quality:</span>
              <span className="font-bold text-white">{telemetry?.signal_quality_pct.toFixed(1) ?? '--'} %</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Uplink Lock:</span>
              <span className="text-emerald-400 font-semibold">{telemetry?.comm_status !== 'LOST' ? 'LOCKED' : 'SEARCHING'}</span>
            </div>
          </div>
        </div>

        {/* ADCS Subsystem */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-space-700 pb-2">
            <span className="font-bold text-slate-200 flex items-center gap-1.5">
              <Compass className="w-4 h-4 text-purple-400" />
              ATTITUDE CONTROL (ADCS)
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-500/20 text-purple-400">
              FINE POINTING
            </span>
          </div>
          <div className="space-y-1.5 text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Attitude Error:</span>
              <span className="font-bold text-white">{telemetry?.attitude_error_deg.toFixed(3) ?? '--'} °</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Angular Rate:</span>
              <span className="font-bold text-white">{telemetry?.angular_rate_deg_s.toFixed(4) ?? '--'} °/s</span>
            </div>
          </div>
        </div>

        {/* Data Handling & Memory */}
        <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-space-700 pb-2">
            <span className="font-bold text-slate-200 flex items-center gap-1.5">
              <Database className="w-4 h-4 text-amber-400" />
              DATA HANDLING (OBDH)
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-400">
              OK
            </span>
          </div>
          <div className="space-y-1.5 text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Solid State Recorder:</span>
              <span className="font-bold text-white">{telemetry?.storage_used_pct.toFixed(2) ?? '--'} %</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Sensor Parity Validity:</span>
              <span className={telemetry?.sensors_valid ? 'text-emerald-400 font-bold' : 'text-red-400 font-bold'}>
                {telemetry?.sensors_valid ? 'VALID' : 'PARITY_ERROR'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Historical Telemetry Frame Query Section */}
      <div className="bg-space-800 border border-space-600 rounded-xl p-4 space-y-3 font-mono text-xs">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-space-700">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-cyan-400" />
            <h3 className="font-bold text-slate-200">HISTORICAL TELEMETRY FRAMES</h3>
          </div>
          <div className="flex items-center space-x-2">
            <select
              value={historyLimit}
              onChange={(e) => setHistoryLimit(Number(e.target.value))}
              className="bg-space-700 border border-space-500 rounded px-2.5 py-1 text-slate-200 text-xs"
            >
              <option value={20}>Last 20 frames</option>
              <option value={50}>Last 50 frames</option>
              <option value={100}>Last 100 frames</option>
            </select>
            <button
              onClick={fetchHistory}
              disabled={isLoadingHistory}
              className="flex items-center space-x-1 px-3 py-1 bg-space-700 hover:bg-space-600 rounded text-cyan-300 border border-space-500 transition"
            >
              <RefreshCw className={`w-3 h-3 ${isLoadingHistory ? 'animate-spin' : ''}`} />
              <span>LOAD</span>
            </button>
          </div>
        </div>

        {historicalData.length > 0 ? (
          <div className="overflow-x-auto max-h-72">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-space-700 text-slate-500 text-[11px]">
                  <th className="py-2 px-3">SIM_T (s)</th>
                  <th className="py-2 px-3">MODE</th>
                  <th className="py-2 px-3">TEMP (°C)</th>
                  <th className="py-2 px-3">BATTERY (%)</th>
                  <th className="py-2 px-3">BUS (V)</th>
                  <th className="py-2 px-3">DRAW (A)</th>
                  <th className="py-2 px-3">COMM</th>
                  <th className="py-2 px-3">POINT_ERR (°)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-space-700/60 text-slate-300">
                {historicalData.map((row, idx) => (
                  <tr key={idx} className="hover:bg-space-700/40 transition">
                    <td className="py-1.5 px-3 font-semibold text-cyan-300">{row.timestamp_sim.toFixed(1)}</td>
                    <td className="py-1.5 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        row.mode === 'SAFE_MODE' ? 'bg-red-500/20 text-red-400' : 'bg-slate-700 text-slate-300'
                      }`}>
                        {row.mode}
                      </span>
                    </td>
                    <td className={`py-1.5 px-3 ${row.temperature_c >= 75.0 ? 'text-red-400 font-bold' : ''}`}>
                      {row.temperature_c.toFixed(2)}
                    </td>
                    <td className="py-1.5 px-3">{row.battery_soc_pct.toFixed(1)}</td>
                    <td className="py-1.5 px-3">{row.bus_voltage_v.toFixed(2)}</td>
                    <td className="py-1.5 px-3">{row.current_draw_a.toFixed(2)}</td>
                    <td className="py-1.5 px-3">{row.comm_status}</td>
                    <td className="py-1.5 px-3">{row.attitude_error_deg.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-slate-500">
            Click 'LOAD' to fetch stored telemetry records from SQLite database.
          </div>
        )}
      </div>
    </div>
  );
};