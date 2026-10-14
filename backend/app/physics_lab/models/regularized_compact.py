"""
Models D1, D2, and D3: Regularized and Screened Compact-Object Formulations
Implements:
- Model D1: Hurwitz-Zeta Kernel with Universal Nath Mass Scaling R0(M) = alpha * gamma * sqrt(GM)
- Model D2: Regularized Compact-Object Potential with Dynamical Planck-Scale UV Cutoff r0(M) = (l_P^2 * R_s)^(1/3)
- Model D3: Environmentally Screened Non-Local Gravity with S(g_bar) acceleration screening
"""

from typing import Dict, Any, Optional
import numpy as np
from scipy.special import zeta
from app.physics_lab.models.base import BasePhysicsModel

G_SI = 6.67430e-11
C_SI = 299792458.0
PLANCK_LENGTH_SI = 1.616255e-35  # m


def compute_hurwitz_kernel(R: float, R0: float, p: float = 2.14) -> float:
    """
    Normalized Hurwitz-zeta deformation kernel:
    Kp(R) = zeta(p, 1 + R / R0) / zeta(p)
    """
    if R < 0.0 or R0 <= 0.0:
        return 1.0
    xi = R / R0
    z_val = float(zeta(p, 1.0 + xi))
    z0_val = float(zeta(p, 1.0))
    if z0_val <= 0.0 or not np.isfinite(z_val):
        return 1.0
    return float(z_val / z0_val)


class HurwitzMassScaledModel(BasePhysicsModel):
    """
    Model D1: Hurwitz-zeta kernel with universal Nath mass scaling.
    R0(M) = alpha * gamma * sqrt(GM)
    g(R) = (GM / R^2) * [1 / Kp(R)]
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        params = parameters or {}
        params.setdefault("G", G_SI)
        params.setdefault("p", 2.14)
        params.setdefault("alpha", 38000.0)
        params.setdefault("gamma", 5.8557)

        super().__init__(
            model_id="MODEL-D1-HURWITZ-MASS-SCALED",
            model_version="1.0.0",
            display_name="Hurwitz-Zeta Kernel with Nath Mass Scaling",
            parameters=params,
        )

    def validate_parameters(self) -> None:
        p = self.parameters.get("p", 2.14)
        alpha = self.parameters.get("alpha", 38000.0)
        gamma = self.parameters.get("gamma", 5.8557)
        if p <= 1.0:
            raise ValueError(f"Zeta exponent p must be > 1.0 for convergence, got {p}")
        if alpha <= 0.0 or gamma <= 0.0:
            raise ValueError("alpha and gamma must be strictly positive")

    def compute_R0(self, M: float) -> float:
        G = self.parameters["G"]
        alpha = self.parameters["alpha"]
        gamma = self.parameters["gamma"]
        return float(alpha * gamma * np.sqrt(G * M))

    def evaluate_potential(self, r: float, M: float) -> float:
        if r <= 0.0:
            raise ValueError(f"Radius r={r} <= 0")
        G = self.parameters["G"]
        R0 = self.compute_R0(M)
        p = self.parameters["p"]
        Kp = compute_hurwitz_kernel(r, R0, p)
        return -float((G * M / r) / Kp)

    def evaluate_radial_acceleration(self, r: float, M: float) -> float:
        if r <= 0.0:
            raise ValueError(f"Radius r={r} <= 0")
        G = self.parameters["G"]
        R0 = self.compute_R0(M)
        p = self.parameters["p"]
        Kp = compute_hurwitz_kernel(r, R0, p)
        # gobs = gbar / Kp
        return float((G * M / (r**2)) / Kp)

    def circular_orbital_speed(self, r: float, M: float) -> Optional[float]:
        if r <= 0.0 or M <= 0.0:
            return None
        g_accel = self.evaluate_radial_acceleration(r, M)
        return float(np.sqrt(r * g_accel))


class RegularizedUVCutoffModel(BasePhysicsModel):
    """
    Model D2: Regularized compact-object formulation with Planck-scale UV cutoff.
    r0(M) = (l_P^2 * Rs)^(1/3) = (2 * G * l_P^2 / c^2)^(1/3) * M^(1/3)
    Phi_reg(R) = - (GM / sqrt(R^2 + r0^2)) * Kp(sqrt(R^2 + r0^2) / R0)
    Ensures finite non-divergent de Sitter core at R -> 0 with zero central force.
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        params = parameters or {}
        params.setdefault("G", G_SI)
        params.setdefault("c", C_SI)
        params.setdefault("l_P", PLANCK_LENGTH_SI)
        params.setdefault("p", 2.14)
        params.setdefault("alpha", 38000.0)
        params.setdefault("gamma", 5.8557)
        params.setdefault("r0_override", None)  # Allow testing with explicit r0

        super().__init__(
            model_id="MODEL-D2-REGULARIZED-UV-CUTOFF",
            model_version="1.0.0",
            display_name="Regularized Compact Object with Planck UV Cutoff",
            parameters=params,
        )

    def validate_parameters(self) -> None:
        p = self.parameters.get("p", 2.14)
        if p <= 1.0:
            raise ValueError(f"p must be > 1.0, got {p}")

    def compute_r0(self, M: float) -> float:
        if self.parameters.get("r0_override") is not None:
            return float(self.parameters["r0_override"])
        G = self.parameters["G"]
        c = self.parameters["c"]
        l_P = self.parameters["l_P"]
        Rs = (2.0 * G * M) / (c**2)
        return float(((l_P**2) * Rs) ** (1.0 / 3.0))

    def compute_R0(self, M: float) -> float:
        G = self.parameters["G"]
        alpha = self.parameters["alpha"]
        gamma = self.parameters["gamma"]
        return float(alpha * gamma * np.sqrt(G * M))

    def evaluate_potential(self, r: float, M: float) -> float:
        G = self.parameters["G"]
        r0 = self.compute_r0(M)
        R0 = self.compute_R0(M)
        p = self.parameters["p"]

        r_eff = float(np.sqrt(r**2 + r0**2))
        Kp = compute_hurwitz_kernel(r_eff, R0, p)
        return -float((G * M / r_eff) * Kp)

    def evaluate_radial_acceleration(self, r: float, M: float) -> float:
        """
        g(r) = -dPhi_reg/dr
        At r = 0, g(0) = 0 exactly due to even symmetry of sqrt(r^2 + r0^2).
        """
        if r == 0.0:
            return 0.0
        # High-accuracy numerical gradient of regularized potential
        h = max(1.0e-5 * r, 1.0e-6)
        phi_plus = self.evaluate_potential(r + h, M)
        phi_minus = self.evaluate_potential(max(0.0, r - h), M)
        return float(-(phi_plus - phi_minus) / (2.0 * h))

    def circular_orbital_speed(self, r: float, M: float) -> Optional[float]:
        if r <= 0.0 or M <= 0.0:
            return 0.0
        g_accel = self.evaluate_radial_acceleration(r, M)
        if g_accel <= 0.0:
            return None
        return float(np.sqrt(r * g_accel))


class ScreenedNonlocalModel(BasePhysicsModel):
    """
    Model D3: Environmentally screened non-local gravitational model.
    S(gbar) = [1 + (gbar / g_dagger)^2]^(-1)
    gobs(R) = gbar(R) + S(gbar) * [gbar(R) / Kp(R) - gbar(R)]
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        params = parameters or {}
        params.setdefault("G", G_SI)
        params.setdefault("p", 2.14)
        params.setdefault("alpha", 38000.0)
        params.setdefault("gamma", 5.8557)
        params.setdefault("g_dagger", 1.2e-10)  # Galactic critical acceleration [m s^-2]

        super().__init__(
            model_id="MODEL-D3-SCREENED-NONLOCAL",
            model_version="1.0.0",
            display_name="Environmentally Screened Non-Local Gravity",
            parameters=params,
        )

    def validate_parameters(self) -> None:
        g_dagger = self.parameters.get("g_dagger", 1.2e-10)
        if g_dagger <= 0.0:
            raise ValueError(f"g_dagger must be positive, got {g_dagger}")

    def compute_R0(self, M: float) -> float:
        G = self.parameters["G"]
        alpha = self.parameters["alpha"]
        gamma = self.parameters["gamma"]
        return float(alpha * gamma * np.sqrt(G * M))

    def screening_factor(self, gbar: float) -> float:
        g_dagger = self.parameters["g_dagger"]
        return float(1.0 / (1.0 + ((gbar / g_dagger)**2)))

    def evaluate_potential(self, r: float, M: float) -> float:
        if r <= 0.0:
            raise ValueError(f"Radius r={r} <= 0")
        G = self.parameters["G"]
        return -float((G * M) / r)

    def evaluate_radial_acceleration(self, r: float, M: float) -> float:
        if r <= 0.0:
            raise ValueError(f"Radius r={r} <= 0")
        G = self.parameters["G"]
        R0 = self.compute_R0(M)
        p = self.parameters["p"]

        gbar = float((G * M) / (r**2))
        Kp = compute_hurwitz_kernel(r, R0, p)
        g_bare = gbar / Kp

        S = self.screening_factor(gbar)
        return float(gbar + S * (g_bare - gbar))

    def circular_orbital_speed(self, r: float, M: float) -> Optional[float]:
        if r <= 0.0 or M <= 0.0:
            return None
        g_accel = self.evaluate_radial_acceleration(r, M)
        return float(np.sqrt(r * g_accel))
