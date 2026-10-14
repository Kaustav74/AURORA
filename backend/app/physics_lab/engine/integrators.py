"""
AURORA Physics Lab - Numerical Integrators
Provides high-accuracy ODE solvers:
- RK4 (Fixed-step 4th order Runge-Kutta)
- Dormand-Prince 5(4) / RK45 (Adaptive step with local error control)
- Velocity-Verlet (Symplectic integrator for conservative central force dynamics)
"""

from abc import ABC, abstractmethod
from typing import Callable, Tuple, Dict, Any, Optional
import numpy as np


class BaseIntegrator(ABC):
    """Abstract base class for ODE integrators."""

    @abstractmethod
    def step(
        self,
        f: Callable[[float, np.ndarray], np.ndarray],
        t: float,
        y: np.ndarray,
        dt: float
    ) -> Tuple[float, np.ndarray, float, Dict[str, Any]]:
        """
        Advance state y at time t by dt.
        Returns: (t_next, y_next, dt_actual, stats)
        """
        pass


class RK4Integrator(BaseIntegrator):
    """Classical 4th-order Runge-Kutta fixed-step integrator."""

    def step(
        self,
        f: Callable[[float, np.ndarray], np.ndarray],
        t: float,
        y: np.ndarray,
        dt: float
    ) -> Tuple[float, np.ndarray, float, Dict[str, Any]]:
        k1 = f(t, y)
        k2 = f(t + 0.5 * dt, y + 0.5 * dt * k1)
        k3 = f(t + 0.5 * dt, y + 0.5 * dt * k2)
        k4 = f(t + dt, y + dt * k3)

        y_next = y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        t_next = t + dt
        return t_next, y_next, dt, {"method": "RK4", "error_estimate": 0.0, "rejected_steps": 0}


class DormandPrinceIntegrator(BaseIntegrator):
    """
    Dormand-Prince 5(4) adaptive step-size integrator (equivalent to DOPRI5 / RK45).
    Features Butcher tableau coefficients with embedded 4th-order local error estimation.
    """

    # Butcher tableau coefficients for DOPRI5
    a21 = 1.0 / 5.0
    a31, a32 = 3.0 / 40.0, 9.0 / 40.0
    a41, a42, a43 = 44.0 / 45.0, -56.0 / 15.0, 32.0 / 9.0
    a51, a52, a53, a54 = 19372.0 / 6561.0, -25360.0 / 2187.0, 64448.0 / 6561.0, -212.0 / 729.0
    a61, a62, a63, a64, a65 = 9017.0 / 3168.0, -355.0 / 33.0, 46732.0 / 5247.0, 49.0 / 176.0, -5103.0 / 18656.0
    a71, a72, a73, a74, a75, a76 = 35.0 / 384.0, 0.0, 500.0 / 1113.0, 125.0 / 192.0, -2187.0 / 6784.0, 11.0 / 84.0

    # 5th-order weights
    b = np.array([35.0 / 384.0, 0.0, 500.0 / 1113.0, 125.0 / 192.0, -2187.0 / 6784.0, 11.0 / 84.0, 0.0])

    # 4th-order embedded weights for error estimation
    b_star = np.array([5179.0 / 57600.0, 0.0, 7571.0 / 16695.0, 393.0 / 640.0, -92097.0 / 339200.0, 187.0 / 2100.0, 1.0 / 40.0])

    def __init__(
        self,
        rtol: float = 1.0e-8,
        atol: float = 1.0e-10,
        dt_min: float = 1.0e-8,
        dt_max: float = 3600.0,
        safety: float = 0.9
    ):
        self.rtol = rtol
        self.atol = atol
        self.dt_min = dt_min
        self.dt_max = dt_max
        self.safety = safety

    def step(
        self,
        f: Callable[[float, np.ndarray], np.ndarray],
        t: float,
        y: np.ndarray,
        dt: float
    ) -> Tuple[float, np.ndarray, float, Dict[str, Any]]:
        rejected = 0
        current_dt = min(max(dt, self.dt_min), self.dt_max)

        while True:
            k1 = f(t, y)
            k2 = f(t + current_dt * (1.0 / 5.0), y + current_dt * (self.a21 * k1))
            k3 = f(t + current_dt * (3.0 / 10.0), y + current_dt * (self.a31 * k1 + self.a32 * k2))
            k4 = f(t + current_dt * (4.0 / 5.0), y + current_dt * (self.a41 * k1 + self.a42 * k2 + self.a43 * k3))
            k5 = f(t + current_dt * (8.0 / 9.0), y + current_dt * (self.a51 * k1 + self.a52 * k2 + self.a53 * k3 + self.a54 * k4))
            k6 = f(t + current_dt, y + current_dt * (self.a61 * k1 + self.a62 * k2 + self.a63 * k3 + self.a64 * k4 + self.a65 * k5))

            # 5th-order candidate solution
            y_5 = y + current_dt * (
                self.b[0] * k1 + self.b[1] * k2 + self.b[2] * k3 +
                self.b[3] * k4 + self.b[4] * k5 + self.b[5] * k6
            )

            # Evaluate FSAL (First Same As Last) 7th stage
            k7 = f(t + current_dt, y_5)

            # 4th-order candidate solution
            y_4 = y + current_dt * (
                self.b_star[0] * k1 + self.b_star[1] * k2 + self.b_star[2] * k3 +
                self.b_star[3] * k4 + self.b_star[4] * k5 + self.b_star[5] * k6 + self.b_star[6] * k7
            )

            # Truncation error vector
            err = np.abs(y_5 - y_4)
            scale = self.atol + self.rtol * np.maximum(np.abs(y), np.abs(y_5))
            err_ratio = float(np.max(err / scale))

            if err_ratio <= 1.0 or current_dt <= self.dt_min:
                # Step accepted
                t_next = t + current_dt
                # Next recommended step size
                if err_ratio > 0.0:
                    factor = self.safety * (err_ratio ** -0.2)
                    next_dt = min(max(factor * current_dt, 0.2 * current_dt), 5.0 * current_dt)
                else:
                    next_dt = 2.0 * current_dt
                next_dt = min(max(next_dt, self.dt_min), self.dt_max)

                stats = {
                    "method": "DORMAN_PRINCE_54",
                    "error_estimate": err_ratio,
                    "rejected_steps": rejected,
                    "next_dt": next_dt
                }
                return t_next, y_5, current_dt, stats
            else:
                # Step rejected, shrink step size
                rejected += 1
                factor = max(self.safety * (err_ratio ** -0.25), 0.1)
                current_dt = max(factor * current_dt, self.dt_min)
                if rejected > 50:
                    raise RuntimeError(
                        f"Dormand-Prince solver failed to converge: step size collapsed to {current_dt} at t={t}"
                    )


class SymplecticVerletIntegrator(BaseIntegrator):
    """
    Symplectic Velocity-Verlet integrator for conservative central force orbital dynamics:
    r_{n+1} = r_n + v_n * dt + 0.5 * a_n * dt^2
    v_{n+1} = v_n + 0.5 * (a_n + a_{n+1}) * dt
    Preserves phase-space volume and exhibits zero secular energy drift for closed orbits.
    """

    def __init__(self, accel_fn: Optional[Callable[[np.ndarray, np.ndarray], np.ndarray]] = None):
        self.accel_fn = accel_fn

    def step(
        self,
        f: Callable[[float, np.ndarray], np.ndarray],
        t: float,
        y: np.ndarray,
        dt: float
    ) -> Tuple[float, np.ndarray, float, Dict[str, Any]]:
        # State vector: [x, y, z, vx, vy, vz, m, m_prop]
        pos = y[0:3]
        vel = y[3:6]
        extras = y[6:]

        # Half-step velocity with current acceleration
        ydot = f(t, y)
        a_current = ydot[3:6]
        pos_next = pos + vel * dt + 0.5 * a_current * (dt**2)

        # Compute next acceleration
        y_mid = np.concatenate([pos_next, vel, extras])
        ydot_next = f(t + dt, y_mid)
        a_next = ydot_next[3:6]

        vel_next = vel + 0.5 * (a_current + a_next) * dt
        y_next = np.concatenate([pos_next, vel_next, extras])

        return t + dt, y_next, dt, {"method": "SYMPLECTIC_VERLET", "error_estimate": 0.0, "rejected_steps": 0}
