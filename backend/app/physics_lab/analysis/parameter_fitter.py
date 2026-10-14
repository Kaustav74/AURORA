"""
AURORA Physics Lab - Parameter Fitting & Sensitivity Sweep Engine
Implements:
- Bounded parameter estimation (e.g. R0, p) against reference or synthetic observations
- Parameter sweep jobs across bounded grids
- Residual variance calculation
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
import time
import numpy as np
from scipy.optimize import minimize
from app.physics_lab.models.registry import PhysicsModelRegistry
from app.physics_lab.engine.propagator import OrbitPropagator


class ParameterFitterEngine:
    """
    Performs sensitivity analysis, parameter sweeps, and objective fitting.
    """

    @classmethod
    def run_parameter_sweep(
        cls,
        model_id: str,
        param_name: str,
        param_values: List[float],
        base_parameters: Dict[str, Any],
        initial_position: List[float],
        initial_velocity: List[float],
        central_mass: float,
        duration_seconds: float = 3600.0,
    ) -> Dict[str, Any]:
        """
        Sweep a chosen parameter across values and record resulting trajectory statistics.
        """
        results: List[Dict[str, Any]] = []
        pos = np.array(initial_position, dtype=np.float64)
        vel = np.array(initial_velocity, dtype=np.float64)

        for val in param_values:
            params = dict(base_parameters)
            params[param_name] = float(val)

            try:
                model_inst = PhysicsModelRegistry.create_model_instance(model_id, parameters=params)
                propagator = OrbitPropagator(
                    model=model_inst,
                    central_mass=central_mass,
                    integrator_name="DORMAND_PRINCE"
                )
                sim_out = propagator.propagate(pos, vel, duration_seconds=duration_seconds, decimate_points=100)

                results.append({
                    "param_value": float(val),
                    "closest_approach_m": sim_out["closest_approach_m"],
                    "farthest_distance_m": sim_out["farthest_distance_m"],
                    "final_speed_mps": sim_out["final_state"]["velocity_mps"],
                    "max_energy_drift": sim_out["max_energy_drift_rel"],
                    "termination_reason": sim_out["termination_reason"],
                    "status": "COMPLETED"
                })
            except Exception as ex:
                results.append({
                    "param_value": float(val),
                    "status": "FAILED",
                    "error": str(ex)
                })

        return {
            "model_id": model_id,
            "swept_parameter": param_name,
            "sweep_count": len(param_values),
            "results": results
        }

    @classmethod
    def fit_single_parameter(
        cls,
        model_id: str,
        param_to_fit: str,
        initial_guess: float,
        bounds: Tuple[float, float],
        target_radial_speeds: List[Dict[str, float]],  # [{"r": ..., "v_target": ...}]
        central_mass: float,
        base_parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Bounded parameter optimization minimizing weighted least squares against target orbital speeds:
        chi2 = sum [ (v_model(r) - v_target)^2 ]
        """
        start_time = time.time()
        base_params = dict(base_parameters or {})

        def objective(x: np.ndarray) -> float:
            test_val = float(x[0])
            params = dict(base_params)
            params[param_to_fit] = test_val
            try:
                model_inst = PhysicsModelRegistry.create_model_instance(model_id, parameters=params)
            except Exception:
                return 1.0e12

            chi2 = 0.0
            for pt in target_radial_speeds:
                r_target = pt["r"]
                v_expected = pt["v_target"]
                v_model = model_inst.circular_orbital_speed(r_target, central_mass)
                if v_model is None or not np.isfinite(v_model):
                    return 1.0e12
                chi2 += (v_model - v_expected)**2

            return float(chi2)

        opt_res = minimize(
            objective,
            x0=[initial_guess],
            bounds=[bounds],
            method="L-BFGS-B"
        )

        elapsed_ms = (time.time() - start_time) * 1000.0

        return {
            "model_id": model_id,
            "parameter": param_to_fit,
            "success": bool(opt_res.success),
            "status_message": str(opt_res.message),
            "initial_guess": initial_guess,
            "optimal_value": float(opt_res.x[0]),
            "final_chi2": float(opt_res.fun),
            "iterations": int(opt_res.nit),
            "bounds": list(bounds),
            "elapsed_ms": elapsed_ms
        }
