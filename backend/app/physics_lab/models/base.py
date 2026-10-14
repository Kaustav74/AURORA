"""
AURORA Physics Lab - Base Physics Model Interface
Provides abstract contracts for all gravitational and dynamical formulations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, List
import numpy as np


class BasePhysicsModel(ABC):
    """
    Abstract base class for all gravitational models in AURORA Physics Lab.
    Enforces SI units, explicit parameter schemas, and rigorous derivative checks.
    """

    def __init__(self, model_id: str, model_version: str, display_name: str, parameters: Dict[str, Any]):
        self.model_id = model_id
        self.model_version = model_version
        self.display_name = display_name
        self.parameters = parameters
        self.validate_parameters()

    @abstractmethod
    def validate_parameters(self) -> None:
        """Validate parameter bounds, types, and physical domains."""
        pass

    @abstractmethod
    def evaluate_potential(self, r: float, M: float) -> float:
        """
        Evaluate gravitational potential Phi(r) per unit test mass [J / kg = m^2 s^-2].
        """
        pass

    @abstractmethod
    def evaluate_radial_acceleration(self, r: float, M: float) -> float:
        """
        Evaluate inward radial gravitational acceleration magnitude g(r) = -dPhi/dr [m s^-2].
        """
        pass

    def evaluate_acceleration_vector(
        self,
        pos: np.ndarray,
        vel: np.ndarray,
        M: float,
        time_sim: float = 0.0
    ) -> np.ndarray:
        """
        Evaluate 3D Cartesian acceleration vector [m s^-2] given position [m] and velocity [m s^-1].
        Default radial central field: a_vec = -g(r) * (r_vec / r).
        Can be overridden for non-central or velocity/phase-dependent forces.
        """
        r = float(np.linalg.norm(pos))
        if r <= 0.0:
            raise ValueError(f"Coordinate singularity encountered: radius r={r} <= 0")
        g_mag = self.evaluate_radial_acceleration(r, M)
        return -g_mag * (pos / r)

    @abstractmethod
    def circular_orbital_speed(self, r: float, M: float) -> Optional[float]:
        """
        Compute circular orbital velocity [m s^-1] at radius r.
        Returns None or raises ValueError if circular orbit is not physically supported.
        """
        pass

    def escape_speed(self, r: float, M: float) -> Optional[float]:
        """
        Compute escape speed [m s^-1] at radius r from energy conservation:
        0.5 * v_esc^2 + Phi(r) = 0 => v_esc = sqrt(-2 * Phi(r))
        Returns None if unbound or Phi(r) >= 0.
        """
        phi = self.evaluate_potential(r, M)
        if phi >= 0.0:
            return None
        return float(np.sqrt(-2.0 * phi))

    def specific_orbital_energy(self, pos: np.ndarray, vel: np.ndarray, M: float) -> float:
        """
        Compute specific mechanical energy [J / kg]: E = 0.5 * v^2 + Phi(r).
        """
        r = float(np.linalg.norm(pos))
        v2 = float(np.dot(vel, vel))
        return 0.5 * v2 + self.evaluate_potential(r, M)

    def specific_angular_momentum(self, pos: np.ndarray, vel: np.ndarray) -> np.ndarray:
        """
        Compute specific angular momentum vector [m^2 s^-1]: h_vec = r_vec x v_vec.
        """
        return np.cross(pos, vel)
