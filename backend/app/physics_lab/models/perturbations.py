"""
Model C: Generalized Kernel Perturbation Model
Implements:
- Distance-weighted acceleration: a_d = K_d * (r / R_ref)^2 * r_hat
- Phase-coupled acceleration: a_p = K_p * sin(phi) * r_hat
- Alignment acceleration: a_s = K_s * (r_hat . s_hat) * s_hat
- Total acceleration: a_vec = a_newton + a_k
Note: Marked as EXPERIMENTAL / UNDER_REVIEW per specification.
"""

from typing import Dict, Any, Optional, List
import numpy as np
from app.physics_lab.models.base import BasePhysicsModel

G_SI = 6.67430e-11


class GeneralizedKernelPerturbationModel(BasePhysicsModel):
    """
    Experimental generalized kernel perturbation formulation (Model C).
    Superimposes distance, phase, and alignment accelerations on central gravity.
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        params = parameters or {}
        params.setdefault("G", G_SI)
        params.setdefault("K_d", 1.0e-7)                  # Distance-weighted magnitude [m s^-2]
        params.setdefault("K_p", 1.0e-7)                  # Phase-coupled magnitude [m s^-2]
        params.setdefault("K_s", 1.0e-7)                  # Alignment magnitude [m s^-2]
        params.setdefault("R_ref", 6.378e6)               # Reference scaling radius [m]
        params.setdefault("s_hat", [1.0, 0.0, 0.0])       # External alignment unit vector
        params.setdefault("enable_distance_term", True)
        params.setdefault("enable_phase_term", True)
        params.setdefault("enable_alignment_term", True)

        super().__init__(
            model_id="MODEL-C-KERNEL-PERTURBATION",
            model_version="1.0.0",
            display_name="Generalized Kernel Perturbations (Experimental)",
            parameters=params,
        )

    def validate_parameters(self) -> None:
        R_ref = self.parameters.get("R_ref", 6.378e6)
        if R_ref <= 0.0:
            raise ValueError(f"Reference radius R_ref must be positive, got {R_ref}")
        s_hat = np.array(self.parameters.get("s_hat", [1.0, 0.0, 0.0]), dtype=np.float64)
        if s_hat.shape != (3,) or np.linalg.norm(s_hat) == 0.0:
            raise ValueError("s_hat must be a non-zero 3D vector")

    def evaluate_potential(self, r: float, M: float) -> float:
        """
        Base gravitational potential: Phi = -GM/r.
        Note: Model C is primarily formulated as an acceleration operator.
        """
        if r <= 0.0:
            raise ValueError(f"Radius r={r} <= 0")
        G = self.parameters["G"]
        return -float((G * M) / r)

    def evaluate_radial_acceleration(self, r: float, M: float) -> float:
        """Central component magnitude."""
        if r <= 0.0:
            raise ValueError(f"Radius r={r} <= 0")
        G = self.parameters["G"]
        return float((G * M) / (r**2))

    def evaluate_acceleration_vector(
        self,
        pos: np.ndarray,
        vel: np.ndarray,
        M: float,
        time_sim: float = 0.0
    ) -> np.ndarray:
        r = float(np.linalg.norm(pos))
        if r <= 0.0:
            raise ValueError(f"Coordinate singularity at r={r} <= 0")

        r_hat = pos / r
        v_norm = float(np.linalg.norm(vel))

        G = self.parameters["G"]
        a_newton = -(G * M / (r**2)) * r_hat

        a_pert = np.zeros(3, dtype=np.float64)

        # 1. Distance-weighted term: K_d * (r / R_ref)^2 * r_hat
        if self.parameters.get("enable_distance_term", True):
            K_d = float(self.parameters["K_d"])
            R_ref = float(self.parameters["R_ref"])
            a_pert += K_d * ((r / R_ref)**2) * r_hat

        # 2. Phase-coupled term: K_p * sin(phi) * r_hat
        if self.parameters.get("enable_phase_term", True) and v_norm > 0.0:
            K_p = float(self.parameters["K_p"])
            cos_phi = float(np.clip(np.dot(r_hat, vel / v_norm), -1.0, 1.0))
            sin_phi = float(np.sqrt(max(0.0, 1.0 - (cos_phi**2))))
            a_pert += K_p * sin_phi * r_hat

        # 3. Alignment term: K_s * (r_hat . s_hat) * s_hat
        if self.parameters.get("enable_alignment_term", True):
            K_s = float(self.parameters["K_s"])
            s_raw = np.array(self.parameters["s_hat"], dtype=np.float64)
            s_hat = s_raw / np.linalg.norm(s_raw)
            proj = float(np.dot(r_hat, s_hat))
            a_pert += K_s * proj * s_hat

        return a_newton + a_pert

    def circular_orbital_speed(self, r: float, M: float) -> Optional[float]:
        """Nominal circular speed approximation in absence of alignment perturbations."""
        G = self.parameters["G"]
        K_d = float(self.parameters.get("K_d", 0.0))
        R_ref = float(self.parameters.get("R_ref", 6.378e6))
        # Net inward force: g_eff = GM/r^2 - K_d * (r/R_ref)^2
        g_eff = (G * M / (r**2)) - K_d * ((r / R_ref)**2)
        if g_eff <= 0.0:
            return None
        return float(np.sqrt(r * g_eff))
