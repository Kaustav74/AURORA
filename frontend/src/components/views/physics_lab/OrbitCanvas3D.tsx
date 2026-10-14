import React, { useRef, useEffect, useState } from 'react';
import { TrajectoryPoint, PhysicsEvent } from '../../../types/physics_lab';
import { RotateCw, Maximize2, Crosshair } from 'lucide-react';

interface OrbitCanvas3DProps {
  trajectory: TrajectoryPoint[];
  events: PhysicsEvent[];
  currentIndex: number;
  rsMeters: number;
  centralMassKg: number;
  onScrubIndex?: (index: number) => void;
}

export const OrbitCanvas3D: React.FC<OrbitCanvas3DProps> = ({
  trajectory,
  events,
  currentIndex,
  rsMeters,
  centralMassKg,
  onScrubIndex,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Camera angles in radians
  const [yaw, setYaw] = useState<number>(0.8);
  const [pitch, setPitch] = useState<number>(0.5);
  const [zoom, setZoom] = useState<number>(1.0);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Reset Camera View
  const handleResetCamera = () => {
    setYaw(0.8);
    setPitch(0.5);
    setZoom(1.0);
  };

  // Drag controls for 3D rotation
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    setYaw((prev) => prev + dx * 0.008);
    setPitch((prev) => Math.max(-1.4, Math.min(1.4, prev + dy * 0.008)));
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.15 : 0.87;
    setZoom((prev) => Math.max(0.05, Math.min(50.0, prev * factor)));
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle high DPI displays
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const cx = width / 2;
    const cy = height / 2;

    // Clear background
    ctx.fillStyle = '#060a12';
    ctx.fillRect(0, 0, width, height);

    // Compute bounding radius across trajectory and key boundaries
    let maxR = Math.max(rsMeters * 6.0, 1000.0);
    if (trajectory.length > 0) {
      for (const p of trajectory) {
        if (p.radius_m > maxR) maxR = p.radius_m;
      }
    }
    const worldScale = (Math.min(width, height) * 0.42 * zoom) / maxR;

    // 3D rotation projection helper: (x, y, z) -> (screenX, screenY)
    const project = (x: number, y: number, z: number): { sx: number; sy: number; sz: number } => {
      // Rotation about Z (Yaw)
      const cosY = Math.cos(yaw);
      const sinY = Math.sin(yaw);
      const x1 = x * cosY - y * sinY;
      const y1 = x * sinY + y * cosY;
      const z1 = z;

      // Rotation about X (Pitch)
      const cosP = Math.cos(pitch);
      const sinP = Math.sin(pitch);
      const y2 = y1 * cosP - z1 * sinP;
      const z2 = y1 * sinP + z1 * cosP;
      const x2 = x1;

      return {
        sx: cx + x2 * worldScale,
        sy: cy - z2 * worldScale,
        sz: y2, // depth for z-sorting
      };
    };

    // Draw background starfield / faint grid
    ctx.strokeStyle = '#111b2b';
    ctx.lineWidth = 1;
    const gridCount = 5;
    const gridStep = maxR / gridCount;
    for (let i = 1; i <= gridCount; i++) {
      const rGrid = i * gridStep * worldScale;
      ctx.beginPath();
      ctx.arc(cx, cy, rGrid, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Draw Coordinate Axes
    const axisLen = maxR * 0.8;
    const axes = [
      { vec: [axisLen, 0, 0], label: '+X', color: 'rgba(239, 68, 68, 0.4)' },
      { vec: [0, axisLen, 0], label: '+Y', color: 'rgba(34, 197, 94, 0.4)' },
      { vec: [0, 0, axisLen], label: '+Z', color: 'rgba(59, 130, 246, 0.4)' },
    ];
    for (const ax of axes) {
      const p = project(ax.vec[0], ax.vec[1], ax.vec[2]);
      ctx.strokeStyle = ax.color;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(p.sx, p.sy);
      ctx.stroke();
      ctx.fillStyle = ax.color;
      ctx.font = '10px monospace';
      ctx.fillText(ax.label, p.sx + 4, p.sy + 4);
    }

    // Draw Relativistic Boundary Rings if RS is non-zero
    if (rsMeters > 0) {
      // 1. ISCO Ring (3.0 * Rs)
      const iscoR = 3.0 * rsMeters;
      ctx.strokeStyle = 'rgba(245, 158, 11, 0.45)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      for (let th = 0; th <= Math.PI * 2; th += 0.05) {
        const pt = project(iscoR * Math.cos(th), iscoR * Math.sin(th), 0);
        if (th === 0) ctx.moveTo(pt.sx, pt.sy);
        else ctx.lineTo(pt.sx, pt.sy);
      }
      ctx.closePath();
      ctx.stroke();

      // 2. Photon Sphere Ring (1.5 * Rs)
      const photonR = 1.5 * rsMeters;
      ctx.strokeStyle = 'rgba(236, 72, 153, 0.55)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([2, 2]);
      ctx.beginPath();
      for (let th = 0; th <= Math.PI * 2; th += 0.05) {
        const pt = project(photonR * Math.cos(th), photonR * Math.sin(th), 0);
        if (th === 0) ctx.moveTo(pt.sx, pt.sy);
        else ctx.lineTo(pt.sx, pt.sy);
      }
      ctx.closePath();
      ctx.stroke();
      ctx.setLineDash([]);

      // 3. Central Compact Object / Black Hole Event Horizon (1.0 * Rs)
      const horizonRadiusPx = Math.max(rsMeters * worldScale, 5);

      // Event horizon outer accretion glow
      const glowGrad = ctx.createRadialGradient(cx, cy, horizonRadiusPx * 0.8, cx, cy, horizonRadiusPx * 2.2);
      glowGrad.addColorStop(0, 'rgba(168, 85, 247, 0.7)');
      glowGrad.addColorStop(0.5, 'rgba(6, 182, 212, 0.25)');
      glowGrad.addColorStop(1, 'rgba(6, 182, 212, 0)');
      ctx.fillStyle = glowGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, horizonRadiusPx * 2.2, 0, Math.PI * 2);
      ctx.fill();

      // Event horizon solid black void
      ctx.fillStyle = '#000000';
      ctx.beginPath();
      ctx.arc(cx, cy, horizonRadiusPx, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#c084fc';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Draw Orbit Trajectory Path
    if (trajectory.length > 1) {
      // Glow background path
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.25)';
      ctx.lineWidth = 4;
      ctx.beginPath();
      for (let i = 0; i < trajectory.length; i++) {
        const pt = project(
          trajectory[i].position[0],
          trajectory[i].position[1],
          trajectory[i].position[2]
        );
        if (i === 0) ctx.moveTo(pt.sx, pt.sy);
        else ctx.lineTo(pt.sx, pt.sy);
      }
      ctx.stroke();

      // Sharp foreground trajectory line
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      for (let i = 0; i < trajectory.length; i++) {
        const pt = project(
          trajectory[i].position[0],
          trajectory[i].position[1],
          trajectory[i].position[2]
        );
        if (i === 0) ctx.moveTo(pt.sx, pt.sy);
        else ctx.lineTo(pt.sx, pt.sy);
      }
      ctx.stroke();

      // Draw Events along trajectory
      for (const ev of events) {
        const pt = project(ev.position[0], ev.position[1], ev.position[2]);
        ctx.fillStyle =
          ev.severity === 'CRITICAL' ? '#ef4444' : ev.severity === 'WARNING' ? '#f59e0b' : '#38bdf8';
        ctx.beginPath();
        ctx.arc(pt.sx, pt.sy, 4.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.fillStyle = '#cbd5e1';
        ctx.font = '9px monospace';
        ctx.fillText(ev.event_type, pt.sx + 6, pt.sy - 4);
      }

      // Draw Active Spacecraft Marker at currentIndex
      const safeIdx = Math.max(0, Math.min(currentIndex, trajectory.length - 1));
      const curr = trajectory[safeIdx];
      const scPt = project(curr.position[0], curr.position[1], curr.position[2]);

      // Spacecraft halo
      ctx.fillStyle = 'rgba(234, 179, 8, 0.35)';
      ctx.beginPath();
      ctx.arc(scPt.sx, scPt.sy, 9, 0, Math.PI * 2);
      ctx.fill();

      // Spacecraft center dot
      ctx.fillStyle = '#eab308';
      ctx.beginPath();
      ctx.arc(scPt.sx, scPt.sy, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Velocity Vector Arrow
      const vMag = curr.speed_mps;
      if (vMag > 0) {
        const vScale = 25.0 / vMag;
        const vTip = project(
          curr.position[0] + curr.velocity[0] * vScale * (maxR * 0.05),
          curr.position[1] + curr.velocity[1] * vScale * (maxR * 0.05),
          curr.position[2] + curr.velocity[2] * vScale * (maxR * 0.05)
        );
        ctx.strokeStyle = '#22c55e';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(scPt.sx, scPt.sy);
        ctx.lineTo(vTip.sx, vTip.sy);
        ctx.stroke();
      }
    }
  }, [trajectory, events, currentIndex, rsMeters, centralMassKg, yaw, pitch, zoom]);

  const activePoint = trajectory[currentIndex] || trajectory[0];

  return (
    <div className="relative w-full h-full flex flex-col bg-space-950 rounded-lg border border-space-700 overflow-hidden select-none">
      {/* 3D Viewport Controls Overlay */}
      <div className="absolute top-3 left-3 z-10 flex items-center space-x-2 bg-space-900/80 backdrop-blur-md px-3 py-1.5 rounded border border-space-700/80 text-xs font-mono text-slate-300">
        <Crosshair className="w-3.5 h-3.5 text-cyan-400" />
        <span>3D ISOMETRIC ORBIT CONSOLE</span>
        <span className="text-slate-500">|</span>
        <span className="text-cyan-300">Drag to Rotate • Scroll to Zoom</span>
      </div>

      <div className="absolute top-3 right-3 z-10 flex items-center space-x-1.5 bg-space-900/80 backdrop-blur-md p-1 rounded border border-space-700/80">
        <button
          onClick={handleResetCamera}
          className="p-1 text-slate-400 hover:text-cyan-300 hover:bg-space-700/60 rounded transition-all"
          title="Reset Camera Orientation"
        >
          <RotateCw className="w-4 h-4" />
        </button>
      </div>

      {/* Main HTML5 Canvas */}
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        className="w-full h-80 sm:h-96 cursor-grab active:cursor-grabbing"
      />

      {/* Orbit Telemetry HUD Bar */}
      {activePoint && (
        <div className="bg-space-900/95 border-t border-space-700 px-4 py-2.5 grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono">
          <div>
            <span className="text-slate-400 block text-[10px]">SIM TIME</span>
            <span className="text-cyan-300 font-bold">t = {activePoint.t_sim_s.toFixed(2)} s</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px]">RADIAL DISTANCE (r)</span>
            <span className="text-slate-100 font-bold">
              {(activePoint.radius_m / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })} km
            </span>
            {rsMeters > 0 && (
              <span className="text-purple-400 text-[10px] block">
                ({(activePoint.radius_m / rsMeters).toFixed(2)} Rs)
              </span>
            )}
          </div>
          <div>
            <span className="text-slate-400 block text-[10px]">ORBITAL SPEED (v)</span>
            <span className="text-emerald-400 font-bold">
              {(activePoint.speed_mps / 1000).toFixed(2)} km/s
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px]">ENERGY DRIFT (ΔE/E)</span>
            <span
              className={`font-bold ${
                Math.abs(activePoint.energy_drift_rel) < 1e-4 ? 'text-cyan-400' : 'text-amber-400'
              }`}
            >
              {activePoint.energy_drift_rel.toExponential(3)}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px]">ANGULAR MOMENTUM (Δh/h)</span>
            <span
              className={`font-bold ${
                Math.abs(activePoint.angular_momentum_drift_rel) < 1e-4 ? 'text-cyan-400' : 'text-amber-400'
              }`}
            >
              {activePoint.angular_momentum_drift_rel.toExponential(3)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
