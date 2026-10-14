"""
AURORA Physics Lab - Spacecraft Propulsion & Maneuver Engine
Implements:
- Tsiolkovsky rocket equation & mass depletion: dm/dt = -T / (I_sp * g_0)
- Finite duration thrust maneuvers (Prograde, Retrograde, Radial, Normal, Fixed)
- Impulsive delta-v maneuvers
- Propellant exhaustion event handling
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np

G0_STANDARD = 9.80665  # Standard gravity [m s^-2]


class PropulsionSubsystem:
    """
    Tracks spacecraft mass, propellant, thruster specs, and active maneuvers.
    """

    def __init__(
        self,
        dry_mass: float = 500.0,
        propellant_mass: float = 200.0,
        thrust_n: float = 100.0,
        isp_seconds: float = 300.0,
        maneuvers: Optional[List[Dict[str, Any]]] = None
    ):
        if dry_mass <= 0.0:
            raise ValueError(f"Spacecraft dry mass must be positive, got {dry_mass}")
        if propellant_mass < 0.0:
            raise ValueError(f"Propellant mass cannot be negative, got {propellant_mass}")
        if thrust_n < 0.0:
            raise ValueError(f"Thrust magnitude must be non-negative, got {thrust_n}")
        if isp_seconds <= 0.0:
            raise ValueError(f"Specific impulse must be positive, got {isp_seconds}")

        self.dry_mass = float(dry_mass)
        self.initial_propellant_mass = float(propellant_mass)
        self.thrust_n = float(thrust_n)
        self.isp_seconds = float(isp_seconds)
        self.exhaust_velocity = self.isp_seconds * G0_STANDARD
        self.mass_flow_rate = (self.thrust_n / self.exhaust_velocity) if self.exhaust_velocity > 0 else 0.0
        self.maneuvers = maneuvers or []

    def get_thrust_and_flow(
        self,
        t: float,
        pos: np.ndarray,
        vel: np.ndarray,
        current_propellant: float
    ) -> Tuple[np.ndarray, float]:
        """
        Evaluate active thrust vector [N] and propellant mass flow rate [kg s^-1] at time t.
        Returns: (thrust_vector, m_dot)
        """
        if current_propellant <= 0.0 or self.thrust_n <= 0.0:
            return np.zeros(3, dtype=np.float64), 0.0

        for m in self.maneuvers:
            m_type = m.get("type", "CONTINUOUS").upper()
            t_start = float(m.get("t_start", 0.0))
            t_end = float(m.get("t_end", t_start))

            if m_type == "CONTINUOUS" and t_start <= t <= t_end:
                thrust_mag = float(m.get("thrust_n", self.thrust_n))
                isp = float(m.get("isp_seconds", self.isp_seconds))
                vex = isp * G0_STANDARD
                mdot = (thrust_mag / vex) if vex > 0 else 0.0

                direction_mode = m.get("direction_mode", "PROGRADE").upper()
                u_dir = self._compute_direction_vector(direction_mode, pos, vel, m.get("fixed_vector"))

                return u_dir * thrust_mag, mdot

        return np.zeros(3, dtype=np.float64), 0.0

    def _compute_direction_vector(
        self,
        mode: str,
        pos: np.ndarray,
        vel: np.ndarray,
        fixed_vec: Optional[List[float]] = None
    ) -> np.ndarray:
        v_norm = np.linalg.norm(vel)
        r_norm = np.linalg.norm(pos)

        v_hat = vel / v_norm if v_norm > 0 else np.array([1.0, 0.0, 0.0])
        r_hat = pos / r_norm if r_norm > 0 else np.array([1.0, 0.0, 0.0])
        h_vec = np.cross(pos, vel)
        h_norm = np.linalg.norm(h_vec)
        h_hat = h_vec / h_norm if h_norm > 0 else np.array([0.0, 0.0, 1.0])

        if mode == "PROGRADE":
            return v_hat
        elif mode == "RETROGRADE":
            return -v_hat
        elif mode == "RADIAL_OUT":
            return r_hat
        elif mode == "RADIAL_IN":
            return -r_hat
        elif mode == "NORMAL":
            return h_hat
        elif mode == "ANTINORMAL":
            return -h_hat
        elif mode == "FIXED" and fixed_vec:
            f = np.array(fixed_vec, dtype=np.float64)
            fn = np.linalg.norm(f)
            return (f / fn) if fn > 0 else v_hat
        return v_hat

    def compute_ideal_delta_v(self, fuel_used: float, initial_mass: float) -> float:
        """Tsiolkovsky delta-v: delta_v = vex * ln(m0 / (m0 - fuel_used))"""
        if fuel_used <= 0.0:
            return 0.0
        final_mass = max(initial_mass - fuel_used, self.dry_mass)
        return float(self.exhaust_velocity * np.log(initial_mass / final_mass))
