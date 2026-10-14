"""
Model A: Classical Point-Mass Newtonian Gravitation
Baseline analytical model for celestial mechanics and orbital verification.
"""

from typing import Dict, Any, Optional
import numpy as np
from app.physics_lab.models.base import BasePhysicsModel

G_SI = 6.67430e-11  # m^3 kg^-1 s^-2


class NewtonianModel(BasePhysicsModel):
    """
    Classical Newtonian point-mass central field:
    Phi(r) = -GM / r
    a_vec = -GM / r^3 * r_vec
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        params = parameters or {}
        params.setdefault("G", G_SI)
        super().__init__(
            model_id="MODEL-A-NEWTONIAN",
            model_version="1.0.0",
            display_name="Classical Point-Mass Newtonian Gravitation",
            parameters=params,
        )

    def validate_parameters(self) -> None:
        G = self.parameters.get("G", G_SI)
        if G <= 0.0:
            raise ValueError(f"Gravitational constant G must be positive, got {G}")

    def evaluate_potential(self, r: float, M: float) -> float:
        if r <= 0.0:
            raise ValueError(f"Coordinate singularity at r={r} <= 0")
        G = self.parameters["G"]
        return -float((G * M) / r)

    def evaluate_radial_acceleration(self, r: float, M: float) -> float:
        if r <= 0.0:
            raise ValueError(f"Coordinate singularity at r={r} <= 0")
        G = self.parameters["G"]
        return float((G * M) / (r**2))

    def circular_orbital_speed(self, r: float, M: float) -> Optional[float]:
        if r <= 0.0 or M <= 0.0:
            return None
        G = self.parameters["G"]
        return float(np.sqrt((G * M) / r))

    def orbital_period(self, r: float, M: float) -> Optional[float]:
        v_c = self.circular_orbital_speed(r, M)
        if not v_c or v_c <= 0.0:
            return None
        return float((2.0 * np.pi * r) / v_c)
