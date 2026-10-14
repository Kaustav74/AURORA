"""
Model B: Normalized Ramanujan-Inspired p-Series Deformation (Opening Formulation)
Implements:
- K_{p,r}(s) = sum_{k=1}^N exp(-pi*k^2/p) / (k+r)^s
- K_hat(R) = K(R) / K(R_ref)
- Phi(R) = -GM/R * K_hat(R)
- a_vec(R) = -GM * [K_hat(R)/R^2 - K_hat'(R)/R] * r_hat
- Analytical derivative dK/dR and independent finite-difference check
- Non-absolute value circular speed validation
- Mathematical horizon-approach indicator H(R)
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np
from app.physics_lab.models.base import BasePhysicsModel

G_SI = 6.67430e-11


class RamanujanPSeriesOpeningModel(BasePhysicsModel):
    """
    Ramanujan-inspired p-series deformation kernel model (Model B).
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        params = parameters or {}
        params.setdefault("G", G_SI)
        params.setdefault("R0", 1.0e6)          # Characteristic scale length [m]
        params.setdefault("s", 2.0)            # Dirichlet exponent Re(s) > 1
        params.setdefault("r", 0.0)            # Regularization offset
        params.setdefault("R_ref", 1.0e7)      # Reference radius for normalization [m]
        params.setdefault("N_terms", 500)      # Series summation truncation
        params.setdefault("R_far", 1.0e9)      # Asymptotic reference for horizon indicator

        super().__init__(
            model_id="MODEL-B-RAMANUJAN-PSERIES-OPENING",
            model_version="1.0.0",
            display_name="Normalized Ramanujan-Inspired p-Series Deformation",
            parameters=params,
        )

        # Cache normalization factor K(R_ref)
        self._K_ref = self._compute_unnormalized_K(self.parameters["R_ref"])

    def validate_parameters(self) -> None:
        G = self.parameters.get("G", G_SI)
        R0 = self.parameters.get("R0", 1.0e6)
        s = self.parameters.get("s", 2.0)
        r = self.parameters.get("r", 0.0)
        R_ref = self.parameters.get("R_ref", 1.0e7)
        N_terms = self.parameters.get("N_terms", 500)

        if G <= 0.0:
            raise ValueError(f"G must be positive, got {G}")
        if R0 <= 0.0:
            raise ValueError(f"R0 must be strictly positive, got {R0}")
        if s <= 1.0:
            raise ValueError(f"Re(s) must be > 1 for Dirichlet absolute convergence, got {s}")
        if r < 0.0 and r.is_integer():
            raise ValueError(f"r must not be a negative integer to prevent singular denominators, got {r}")
        if R_ref <= 0.0:
            raise ValueError(f"Reference radius R_ref must be positive, got {R_ref}")
        if N_terms < 10:
            raise ValueError(f"N_terms must be at least 10 for series truncation, got {N_terms}")

    def _compute_unnormalized_K(self, R: float) -> float:
        """
        Compute unnormalized series sum K_{p(R), r}(s):
        sum_{k=1}^N exp(-pi * k^2 / p) / (k + r)^s
        where p = R / R0.
        """
        if R <= 0.0:
            raise ValueError(f"Radius R must be positive, got {R}")

        R0 = self.parameters["R0"]
        s = self.parameters["s"]
        r = self.parameters["r"]
        N = int(self.parameters["N_terms"])

        p = R / R0
        k = np.arange(1, N + 1, dtype=np.float64)

        # Exponent -pi * k^2 / p
        exponent = -np.pi * (k**2) / p
        # Mask out underflow to prevent numerical noise
        valid_mask = exponent > -700.0
        if not np.any(valid_mask):
            return 0.0

        k_valid = k[valid_mask]
        exp_terms = np.exp(exponent[valid_mask])
        denominators = (k_valid + r)**s

        return float(np.sum(exp_terms / denominators))

    def evaluate_normalized_K(self, R: float) -> float:
        """
        Evaluate normalized kernel:
        K_hat(R) = K_{p(R), r}(s) / K_{p(R_ref), r}(s)
        """
        K_R = self._compute_unnormalized_K(R)
        if self._K_ref <= 0.0:
            raise RuntimeError("Cached K(R_ref) is non-positive or zero.")
        return float(K_R / self._K_ref)

    def evaluate_dK_dR_analytic(self, R: float) -> float:
        """
        Compute analytical radial derivative of unnormalized kernel:
        dK/dR = (1 / R0) * sum_{k=1}^N (pi * k^2 / p^2) * exp(-pi * k^2 / p) / (k + r)^2
        """
        if R <= 0.0:
            raise ValueError(f"Radius R must be positive, got {R}")

        R0 = self.parameters["R0"]
        r = self.parameters["r"]
        N = int(self.parameters["N_terms"])

        p = R / R0
        k = np.arange(1, N + 1, dtype=np.float64)

        exponent = -np.pi * (k**2) / p
        valid_mask = exponent > -700.0
        if not np.any(valid_mask):
            return 0.0

        k_valid = k[valid_mask]
        exp_terms = np.exp(exponent[valid_mask])
        denominators = (k_valid + r)**2

        weights = (np.pi * (k_valid**2)) / (p**2)
        sum_terms = (weights * exp_terms) / denominators

        return float((1.0 / R0) * np.sum(sum_terms))

    def evaluate_normalized_dK_dR(self, R: float) -> float:
        """
        Compute analytical derivative of normalized kernel:
        K_hat'(R) = (dK/dR) / K(R_ref)
        """
        dK_dR = self.evaluate_dK_dR_analytic(R)
        return float(dK_dR / self._K_ref)

    def evaluate_dK_dR_finite_difference(self, R: float, rel_step: float = 1.0e-5) -> float:
        """
        Independent numerical central-difference check of K_hat'(R):
        K_hat'_FD = [K_hat(R + h) - K_hat(R - h)] / (2 * h)
        """
        h = max(rel_step * R, 1.0e-8)
        K_plus = self.evaluate_normalized_K(R + h)
        K_minus = self.evaluate_normalized_K(R - h)
        return float((K_plus - K_minus) / (2.0 * h))

    def evaluate_potential(self, r: float, M: float) -> float:
        """
        Phi(R) = - (GM / R) * K_hat(R)
        """
        if r <= 0.0:
            raise ValueError(f"Coordinate singularity at r={r} <= 0")
        G = self.parameters["G"]
        K_hat = self.evaluate_normalized_K(r)
        return -float((G * M / r) * K_hat)

    def evaluate_radial_acceleration(self, r: float, M: float) -> float:
        """
        Radial inward gravitational acceleration magnitude:
        g(R) = GM * [ K_hat(R) / R^2 - K_hat'(R) / R ]
        """
        if r <= 0.0:
            raise ValueError(f"Coordinate singularity at r={r} <= 0")
        G = self.parameters["G"]
        K_hat = self.evaluate_normalized_K(r)
        dK_hat = self.evaluate_normalized_dK_dR(r)

        g_val = (G * M) * ((K_hat / (r**2)) - (dK_hat / r))
        return float(g_val)

    def circular_orbital_speed(self, r: float, M: float) -> Optional[float]:
        """
        v_circ(R) = sqrt(GM * [ K_hat(R) / R - K_hat'(R) ])
        Strict Rule: Do NOT conceal negative term with abs(). Return None if not supported.
        """
        if r <= 0.0 or M <= 0.0:
            return None
        G = self.parameters["G"]
        K_hat = self.evaluate_normalized_K(r)
        dK_hat = self.evaluate_normalized_dK_dR(r)

        term = (K_hat / r) - dK_hat
        if term <= 0.0:
            # Orbital centrifugal balance cannot be sustained (unphysical or repulsive regime)
            return None

        return float(np.sqrt(G * M * term))

    def horizon_approach_indicator(self, R: float) -> float:
        """
        Mathematical horizon-approach diagnostic H(R):
        H(R) = 1 - K_{p(R), r}(2) / K_{p(R_far), r}(2)
        H(R) -> 1 as R -> 0; H(R) -> 0 as R -> R_far.
        Diagnostic indicator only; not an actual relativistic event horizon.
        """
        R_far = self.parameters.get("R_far", 1.0e9)
        K_R = self._compute_unnormalized_K(R)
        K_far = self._compute_unnormalized_K(R_far)
        if K_far <= 0.0:
            return 1.0
        return float(1.0 - (K_R / K_far))
