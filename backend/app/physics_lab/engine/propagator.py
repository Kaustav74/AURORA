"""
AURORA Physics Lab - Numerical Orbit Propagator
Simulates 3D trajectories around compact objects with event detection,
adaptive error control, propulsion mass tracking, and diagnostic time series.
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
import time
import numpy as np
from app.physics_lab.models.base import BasePhysicsModel
from app.physics_lab.engine.integrators import (
    BaseIntegrator,
    RK4Integrator,
    DormandPrinceIntegrator,
    SymplecticVerletIntegrator,
)
from app.physics_lab.engine.propulsion import PropulsionSubsystem

C_SI = 299792458.0


class OrbitPropagator:
    """
    Precision orbit propagator supporting multiple physics models,
    adaptive solvers, spacecraft propulsion, and event detection.
    """

    def __init__(
        self,
        model: BasePhysicsModel,
        central_mass: float = 1.989e30,
        integrator_name: str = "DORMAND_PRINCE",
        rtol: float = 1.0e-7,
        atol: float = 1.0e-9,
        dt_min: float = 1.0e-5,
        dt_max: float = 3600.0,
        propulsion: Optional[PropulsionSubsystem] = None,
        rs_horizon: Optional[float] = None,
        r_collision: Optional[float] = None,
        r_escape: Optional[float] = None,
        max_steps: int = 50000,
    ):
        self.model = model
        self.central_mass = float(central_mass)
        self.integrator_name = integrator_name.upper()
        self.propulsion = propulsion
        self.max_steps = max_steps

        # Physical boundaries
        G = float(model.parameters.get("G", 6.67430e-11))
        self.rs_horizon = rs_horizon if rs_horizon is not None else (2.0 * G * self.central_mass / (C_SI**2))
        self.r_collision = r_collision if r_collision is not None else self.rs_horizon
        self.r_escape = r_escape

        # Instantiate selected integrator
        if self.integrator_name in ("DORMAND_PRINCE", "RK45", "DOPRI5"):
            self.integrator: BaseIntegrator = DormandPrinceIntegrator(
                rtol=rtol, atol=atol, dt_min=dt_min, dt_max=dt_max
            )
        elif self.integrator_name == "RK4":
            self.integrator = RK4Integrator()
        elif self.integrator_name in ("SYMPLECTIC", "VERLET", "VELOCITY_VERLET"):
            self.integrator = SymplecticVerletIntegrator()
        else:
            raise ValueError(f"Unknown integrator '{integrator_name}'")

    def propagate(
        self,
        initial_position: np.ndarray,
        initial_velocity: np.ndarray,
        duration_seconds: float,
        dt_initial: float = 10.0,
        decimate_points: int = 600,
    ) -> Dict[str, Any]:
        """
        Run complete orbit propagation over duration_seconds.
        """
        start_wall_time = time.time()
        pos = np.array(initial_position, dtype=np.float64)
        vel = np.array(initial_velocity, dtype=np.float64)

        if pos.shape != (3,) or vel.shape != (3,):
            raise ValueError("Position and velocity must be 3D vectors")

        dry_mass = self.propulsion.dry_mass if self.propulsion else 500.0
        prop_mass = self.propulsion.initial_propellant_mass if self.propulsion else 0.0
        total_mass = dry_mass + prop_mass

        # State vector: [x, y, z, vx, vy, vz, total_mass, prop_mass]
        y = np.array([
            pos[0], pos[1], pos[2],
            vel[0], vel[1], vel[2],
            total_mass, prop_mass
        ], dtype=np.float64)

        # Baseline conserved quantities
        e0 = self.model.specific_orbital_energy(pos, vel, self.central_mass)
        h0_vec = self.model.specific_angular_momentum(pos, vel)
        h0_mag = float(np.linalg.norm(h0_vec))

        # ODE derivative function
        def derivatives(t_sim: float, state: np.ndarray) -> np.ndarray:
            r_vec = state[0:3]
            v_vec = state[3:6]
            m_curr = max(state[6], 1.0e-3)
            p_curr = max(state[7], 0.0)

            # Gravitational acceleration from active model
            a_grav = self.model.evaluate_acceleration_vector(r_vec, v_vec, self.central_mass, t_sim)

            # Propulsion force
            if self.propulsion and p_curr > 0.0:
                thrust_vec, mdot = self.propulsion.get_thrust_and_flow(t_sim, r_vec, v_vec, p_curr)
                a_thrust = thrust_vec / m_curr
                dm = -mdot
                dp = -mdot
            else:
                a_thrust = np.zeros(3, dtype=np.float64)
                dm = 0.0
                dp = 0.0

            a_total = a_grav + a_thrust
            return np.array([
                v_vec[0], v_vec[1], v_vec[2],
                a_total[0], a_total[1], a_total[2],
                dm, dp
            ], dtype=np.float64)

        t = 0.0
        dt = float(dt_initial)
        steps_count = 0
        events: List[Dict[str, Any]] = []
        raw_trajectory: List[Dict[str, Any]] = []
        termination_reason = "DURATION_REACHED"

        prev_vr: Optional[float] = None
        fuel_exhausted_logged = False

        # Initial sample
        r_init = float(np.linalg.norm(pos))
        v_init = float(np.linalg.norm(vel))
        raw_trajectory.append(
            self._build_trajectory_frame(
                t=0.0,
                pos=pos,
                vel=vel,
                total_mass=total_mass,
                prop_mass=prop_mass,
                e0=e0,
                h0_mag=h0_mag,
                a_thrust=0.0
            )
        )

        while t < duration_seconds and steps_count < self.max_steps:
            steps_count += 1
            r_curr = float(np.linalg.norm(y[0:3]))

            # Check horizon / collision event
            if self.rs_horizon and r_curr <= self.rs_horizon:
                termination_reason = "HORIZON_CROSSING"
                events.append({
                    "time_sim": t,
                    "event_type": "HORIZON_CROSSING",
                    "severity": "CRITICAL",
                    "description": f"Spacecraft entered Schwarzschild horizon at r={r_curr:.2f} m <= Rs={self.rs_horizon:.2f} m",
                    "position": y[0:3].tolist(),
                    "radius": r_curr
                })
                break

            if self.r_collision and r_curr <= self.r_collision and self.r_collision != self.rs_horizon:
                termination_reason = "COLLISION_BOUNDARY"
                events.append({
                    "time_sim": t,
                    "event_type": "COLLISION_BOUNDARY",
                    "severity": "CRITICAL",
                    "description": f"Spacecraft contacted physical collision boundary at r={r_curr:.2f} m",
                    "position": y[0:3].tolist(),
                    "radius": r_curr
                })
                break

            # Check escape boundary
            if self.r_escape and r_curr >= self.r_escape:
                termination_reason = "ESCAPE_BOUNDARY"
                events.append({
                    "time_sim": t,
                    "event_type": "ESCAPE_BOUNDARY",
                    "severity": "INFO",
                    "description": f"Spacecraft passed outer escape boundary at r={r_curr:.2f} m",
                    "position": y[0:3].tolist(),
                    "radius": r_curr
                })
                break

            # Check fuel exhaustion
            if self.propulsion and y[7] <= 0.0 and not fuel_exhausted_logged:
                fuel_exhausted_logged = True
                events.append({
                    "time_sim": t,
                    "event_type": "PROPELLANT_EXHAUSTED",
                    "severity": "WARNING",
                    "description": "Propellant depleted; active propulsion maneuvers disabled.",
                    "position": y[0:3].tolist(),
                    "radius": r_curr
                })

            # Radial velocity zero-crossing detection (Apsides)
            vr = float(np.dot(y[0:3], y[3:6]) / r_curr)
            if prev_vr is not None:
                if prev_vr < 0.0 and vr >= 0.0:
                    events.append({
                        "time_sim": t,
                        "event_type": "PERIAPSIS_APPROACH",
                        "severity": "INFO",
                        "description": f"Periapsis reached at closest approach r={r_curr:.2f} m",
                        "position": y[0:3].tolist(),
                        "radius": r_curr
                    })
                elif prev_vr > 0.0 and vr <= 0.0:
                    events.append({
                        "time_sim": t,
                        "event_type": "APOAPSIS_REACHED",
                        "severity": "INFO",
                        "description": f"Apoapsis reached at farthest distance r={r_curr:.2f} m",
                        "position": y[0:3].tolist(),
                        "radius": r_curr
                    })
            prev_vr = vr

            # Step integration
            step_dt = min(dt, duration_seconds - t)
            try:
                t_next, y_next, actual_dt, stats = self.integrator.step(derivatives, t, y, step_dt)
            except Exception as ex:
                termination_reason = "SOLVER_FAILURE"
                events.append({
                    "time_sim": t,
                    "event_type": "SOLVER_FAILURE",
                    "severity": "CRITICAL",
                    "description": f"Integrator failed at t={t:.2f} s: {str(ex)}",
                    "position": y[0:3].tolist(),
                    "radius": r_curr
                })
                break

            # Non-finite check
            if not np.all(np.isfinite(y_next)):
                termination_reason = "NON_FINITE_STATE"
                events.append({
                    "time_sim": t,
                    "event_type": "NON_FINITE_STATE",
                    "severity": "CRITICAL",
                    "description": "Encountered NaN or Inf in state vector during numerical step.",
                    "position": y[0:3].tolist(),
                    "radius": r_curr
                })
                break

            t = t_next
            y = y_next
            dt = stats.get("next_dt", dt)

            # Record frame
            a_thrust_mag = 0.0
            if self.propulsion and y[7] > 0.0:
                t_vec, _ = self.propulsion.get_thrust_and_flow(t, y[0:3], y[3:6], y[7])
                a_thrust_mag = float(np.linalg.norm(t_vec) / y[6])

            raw_trajectory.append(
                self._build_trajectory_frame(
                    t=t,
                    pos=y[0:3],
                    vel=y[3:6],
                    total_mass=float(y[6]),
                    prop_mass=float(y[7]),
                    e0=e0,
                    h0_mag=h0_mag,
                    a_thrust=a_thrust_mag
                )
            )

        if steps_count >= self.max_steps and t < duration_seconds:
            termination_reason = "MAX_STEPS_EXCEEDED"
            events.append({
                "time_sim": t,
                "event_type": "MAX_STEPS_EXCEEDED",
                "severity": "WARNING",
                "description": f"Reached maximum allowed integration steps ({self.max_steps}).",
                "position": y[0:3].tolist(),
                "radius": float(np.linalg.norm(y[0:3]))
            })

        # Decimate trajectory points for frontend visualization
        decimated_trajectory = self._decimate_trajectory(raw_trajectory, target_count=decimate_points)

        execution_duration_ms = (time.time() - start_wall_time) * 1000.0

        # Summary statistics
        radii = [f["radius_m"] for f in raw_trajectory]
        min_radius = min(radii) if radii else 0.0
        max_radius = max(radii) if radii else 0.0

        energy_drifts = [f["energy_drift_rel"] for f in raw_trajectory]
        max_energy_drift = max(map(abs, energy_drifts)) if energy_drifts else 0.0

        return {
            "model_id": self.model.model_id,
            "model_version": self.model.model_version,
            "central_mass_kg": self.central_mass,
            "schwarzschild_radius_m": self.rs_horizon,
            "integrator": self.integrator_name,
            "sim_duration_s": t,
            "requested_duration_s": duration_seconds,
            "total_steps": steps_count,
            "raw_points_count": len(raw_trajectory),
            "decimated_points_count": len(decimated_trajectory),
            "termination_reason": termination_reason,
            "execution_duration_ms": execution_duration_ms,
            "closest_approach_m": min_radius,
            "farthest_distance_m": max_radius,
            "max_energy_drift_rel": max_energy_drift,
            "initial_state": {
                "position_m": initial_position.tolist(),
                "velocity_mps": initial_velocity.tolist(),
                "mass_kg": total_mass
            },
            "final_state": {
                "position_m": y[0:3].tolist(),
                "velocity_mps": y[3:6].tolist(),
                "mass_kg": float(y[6]),
                "propellant_kg": float(y[7])
            },
            "events": events,
            "trajectory": decimated_trajectory
        }

    def _build_trajectory_frame(
        self,
        t: float,
        pos: np.ndarray,
        vel: np.ndarray,
        total_mass: float,
        prop_mass: float,
        e0: float,
        h0_mag: float,
        a_thrust: float
    ) -> Dict[str, Any]:
        r = float(np.linalg.norm(pos))
        v = float(np.linalg.norm(vel))

        energy = self.model.specific_orbital_energy(pos, vel, self.central_mass)
        energy_drift = ((energy - e0) / abs(e0)) if abs(e0) > 1.0e-12 else 0.0

        h_vec = self.model.specific_angular_momentum(pos, vel)
        h_mag = float(np.linalg.norm(h_vec))
        h_drift = ((h_mag - h0_mag) / h0_mag) if h0_mag > 1.0e-12 else 0.0

        g_accel = self.model.evaluate_radial_acceleration(r, self.central_mass)

        frame: Dict[str, Any] = {
            "t_sim": round(t, 4),
            "x": round(float(pos[0]), 2),
            "y": round(float(pos[1]), 2),
            "z": round(float(pos[2]), 2),
            "vx": round(float(vel[0]), 3),
            "vy": round(float(vel[1]), 3),
            "vz": round(float(vel[2]), 3),
            "radius_m": round(r, 2),
            "speed_mps": round(v, 3),
            "specific_energy": energy,
            "energy_drift_rel": energy_drift,
            "angular_momentum_mag": h_mag,
            "h_drift_rel": h_drift,
            "total_mass_kg": round(total_mass, 3),
            "propellant_mass_kg": round(prop_mass, 3),
            "grav_acceleration_mps2": round(g_accel, 6),
            "thrust_acceleration_mps2": round(a_thrust, 6)
        }

        # Include horizon indicator if supported by Model B
        if hasattr(self.model, "horizon_approach_indicator"):
            frame["horizon_indicator_H"] = round(self.model.horizon_approach_indicator(r), 6)

        return frame

    def _decimate_trajectory(
        self,
        raw_list: List[Dict[str, Any]],
        target_count: int = 600
    ) -> List[Dict[str, Any]]:
        n = len(raw_list)
        if n <= target_count:
            return raw_list

        step_idx = max(1, n // target_count)
        decimated = [raw_list[i] for i in range(0, n, step_idx)]
        # Always include the exact final point
        if decimated[-1] != raw_list[-1]:
            decimated.append(raw_list[-1])
        return decimated
