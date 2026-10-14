"""
Model E: Relativistic Schwarzschild Geodesic Reference
Implements:
- Schwarzschild radius Rs = 2GM/c^2
- Innermost Stable Circular Orbit r_ISCO = 6GM/c^2
- Photon sphere radius r_photon = 3GM/c^2
- Relativistic radial geodesic equation with -3GM*L^2/(c^2*r^4) precession term
- Analytical perihelion advance: Delta_phi = 6*pi*GM / (c^2 * a * (1 - e^2))
"""

from typing import Dict, Any, Optional
import numpy as np
from app.physics_lab.models.base import BasePhysicsModel

G_SI = 6.67430e-11
C_SI = 299792458.0


class SchwarzschildRelativisticModel(BasePhysicsModel):
    """
    Schwarzschild spacetime relativistic reference model.
    Models test-particle timelike geodesics around a non-rotating, uncharged compact object.
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        params = parameters or {}
        params.setdefault("G", G_SI)
        params.setdefault("c", C_SI)

        super().__init__(
            model_id="MODEL-E-RELATIVISTIC-SCHWARZSCHILD",
            model_version="1.0.0",
            display_name="Relativistic Schwarzschild Geodesic Reference",
            parameters=params,
        )

    def validate_parameters(self) -> None:
        G = self.parameters.get("G", G_SI)
        c = self.parameters.get("c", C_SI)
        if G <= 0.0:
            raise ValueError(f"G must be positive, got {G}")
        if c <= 0.0:
            raise ValueError(f"Speed of light c must be positive, got {c}")

    def schwarzschild_radius(self, M: float) -> float:
        """Rs = 2 * G * M / c^2"""
        G = self.parameters["G"]
        c = self.parameters["c"]
        return float((2.0 * G * M) / (c**2))

    def isco_radius(self, M: float) -> float:
        """Innermost Stable Circular Orbit: r_ISCO = 6 * G * M / c^2 = 3 * Rs"""
        return 3.0 * self.schwarzschild_radius(M)

    def photon_sphere_radius(self, M: float) -> float:
        """Photon sphere: r_ps = 3 * G * M / c^2 = 1.5 * Rs"""
        return 1.5 * self.schwarzschild_radius(M)

    def evaluate_potential(self, r: float, M: float) -> float:
        """
        Effective potential per unit mass:
        Phi(r) = -GM/r with horizon clamping for smooth boundary detection.
        """
        Rs = self.schwarzschild_radius(M)
        r_eff = max(r, 0.5 * Rs) if Rs > 0 else max(r, 1.0)
        G = self.parameters["G"]
        return -float((G * M) / r_eff)

    def evaluate_radial_acceleration(self, r: float, M: float) -> float:
        """
        Radial acceleration magnitude:
        g(r) = GM / r^2
        """
        Rs = self.schwarzschild_radius(M)
        r_eff = max(r, 0.5 * Rs) if Rs > 0 else max(r, 1.0)
        G = self.parameters["G"]
        return float((G * M) / (r_eff**2))

    def evaluate_acceleration_vector(
        self,
        pos: np.ndarray,
        vel: np.ndarray,
        M: float,
        time_sim: float = 0.0
    ) -> np.ndarray:
        """
        Evaluate relativistic geodesic acceleration:
        a_vec = -GM/r^3 * r_vec - (3 * GM * L^2 / (c^2 * r^5)) * r_vec
        where L = ||r_vec x v_vec|| is specific angular momentum.
        """
        r = float(np.linalg.norm(pos))
        Rs = self.schwarzschild_radius(M)
        r_eff = max(r, 0.5 * Rs) if Rs > 0 else max(r, 1.0)
        r_hat = pos / r if r > 0 else np.array([1.0, 0.0, 0.0])

        G = self.parameters["G"]
        c = self.parameters["c"]

        h_vec = np.cross(pos, vel)
        L2 = float(np.dot(h_vec, h_vec))

        # Classical term: -GM/r^2 * r_hat
        a_classical = -(G * M / (r_eff**2)) * r_hat
        # Relativistic post-Newtonian correction causing perihelion precession
        a_relativistic = -(3.0 * G * M * L2 / ((c**2) * (r_eff**4))) * r_hat

        return a_classical + a_relativistic

    def circular_orbital_speed(self, r: float, M: float) -> Optional[float]:
        """
        Circular orbit balancing classical and post-Newtonian acceleration:
        a_grav = GM/r^2 + 3GM L^2 / (c^2 r^4) = v^2 / r
        => v_circ(r) = sqrt(GM / (r - 1.5 * Rs))
        Stable only for r > r_ISCO = 3.0 * Rs.
        """
        r_isco = self.isco_radius(M)
        if r <= r_isco:
            # Below ISCO, circular orbits are unstable to plunge
            return None
        G = self.parameters["G"]
        Rs = self.schwarzschild_radius(M)
        denom = r - 1.5 * Rs
        if denom <= 0.0:
            return None
        return float(np.sqrt((G * M) / denom))

    def analytical_perihelion_advance(self, a: float, e: float, M: float) -> float:
        """
        Analytical Einstein perihelion advance per revolution [radians]:
        Delta_phi = 6 * pi * G * M / (c^2 * a * (1 - e^2))
        """
        G = self.parameters["G"]
        c = self.parameters["c"]
        denominator = (c**2) * a * (1.0 - (e**2))
        if denominator <= 0.0:
            return 0.0
        return float((6.0 * np.pi * G * M) / denominator)
