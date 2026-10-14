"""
AURORA Physics Lab - Anomaly Detection Engine
Evaluates trajectory time-series and identifies numerical failures,
energy/momentum invariant drifts, boundary crossings, propulsion inconsistencies,
and model disagreements.
"""

from typing import Dict, Any, List, Optional
import uuid
import numpy as np


class AnomalyDetectorEngine:
    """
    Automated scientific anomaly detector analyzing simulation runs.
    """

    def __init__(
        self,
        energy_drift_threshold: float = 1.0e-3,
        angular_momentum_drift_threshold: float = 1.0e-4,
        max_position_residual_threshold: float = 1.0e5,  # m
    ):
        self.energy_drift_threshold = energy_drift_threshold
        self.angular_momentum_drift_threshold = angular_momentum_drift_threshold
        self.max_position_residual_threshold = max_position_residual_threshold

    def analyze_simulation_run(
        self,
        experiment_id: str,
        sim_result: Dict[str, Any],
        reference_result: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run complete battery of detectors over a completed simulation result.
        """
        findings: List[Dict[str, Any]] = []
        trajectory = sim_result.get("trajectory", [])
        events = sim_result.get("events", [])
        model_id = sim_result.get("model_id", "UNKNOWN")
        rs_horizon = sim_result.get("schwarzschild_radius_m", 0.0)

        # 1. Detector Family A: Numerical Integrity & Termination
        termination_reason = sim_result.get("termination_reason", "DURATION_REACHED")
        if termination_reason in ("NON_FINITE_STATE", "SOLVER_FAILURE"):
            findings.append({
                "id": f"ANO-{uuid.uuid4().hex[:8].upper()}",
                "time_sim": sim_result.get("sim_duration_s", 0.0),
                "experiment_id": experiment_id,
                "model_id": model_id,
                "category": "NUMERICAL_FAILURE",
                "severity": "CRITICAL",
                "title": f"Numerical Solver Failure ({termination_reason})",
                "explanation": "State vector diverged or became non-finite during numerical integration.",
                "detection_rule": "state_vector_finite_check",
                "observed_value": termination_reason,
                "reference_value": "DURATION_REACHED",
                "residual": None,
                "threshold": "all_finite",
                "status": "NEW",
                "recommended_action": "Rerun with smaller maximum step size or tighter adaptive tolerances."
            })

        # 2. Detector Family B: Physical Boundary & Horizon Crossings
        for evt in events:
            evt_type = evt.get("event_type")
            if evt_type == "HORIZON_CROSSING":
                findings.append({
                    "id": f"ANO-{uuid.uuid4().hex[:8].upper()}",
                    "time_sim": evt.get("time_sim", 0.0),
                    "experiment_id": experiment_id,
                    "model_id": model_id,
                    "category": "PHYSICAL_BOUNDARY",
                    "severity": "CRITICAL",
                    "title": "Schwarzschild Horizon Infall Crossing",
                    "explanation": f"Trajectory plunged inside the compact-object event horizon (r <= Rs = {rs_horizon:.2f} m).",
                    "detection_rule": "radius <= rs_horizon",
                    "observed_value": evt.get("radius"),
                    "reference_value": rs_horizon,
                    "residual": (evt.get("radius", 0.0) - rs_horizon),
                    "threshold": rs_horizon,
                    "status": "NEW",
                    "recommended_action": "Inspect orbital energy and periapsis conditions; consider retrograde burn prior to ISCO."
                })
            elif evt_type == "COLLISION_BOUNDARY":
                findings.append({
                    "id": f"ANO-{uuid.uuid4().hex[:8].upper()}",
                    "time_sim": evt.get("time_sim", 0.0),
                    "experiment_id": experiment_id,
                    "model_id": model_id,
                    "category": "PHYSICAL_BOUNDARY",
                    "severity": "CRITICAL",
                    "title": "Central Body Surface Impact",
                    "explanation": "Spacecraft intercepted the physical collision radius of the central primary.",
                    "detection_rule": "radius <= r_collision",
                    "observed_value": evt.get("radius"),
                    "reference_value": "r_surface",
                    "residual": None,
                    "threshold": "r_collision",
                    "status": "NEW",
                    "recommended_action": "Perform orbital raising maneuver."
                })

        # 3. Detector Family C: Invariant Conservation Drift
        # Only evaluate energy drift if no active maneuvers or non-conservative perturbations
        has_active_burn = any(f.get("thrust_acceleration_mps2", 0.0) > 0.0 for f in trajectory)
        is_conservative_model = model_id in (
            "MODEL-A-NEWTONIAN",
            "MODEL-B-RAMANUJAN-PSERIES-OPENING",
            "MODEL-D1-HURWITZ-MASS-SCALED",
            "MODEL-D2-REGULARIZED-UV-CUTOFF"
        )

        if is_conservative_model and not has_active_burn and trajectory:
            for frame in trajectory:
                e_drift = abs(frame.get("energy_drift_rel", 0.0))
                if e_drift > self.energy_drift_threshold:
                    findings.append({
                        "id": f"ANO-{uuid.uuid4().hex[:8].upper()}",
                        "time_sim": frame.get("t_sim", 0.0),
                        "experiment_id": experiment_id,
                        "model_id": model_id,
                        "category": "NUMERICAL_CONVERGENCE",
                        "severity": "WARNING",
                        "title": f"Specific Mechanical Energy Drift Exceeded ({e_drift:.2e})",
                        "explanation": (
                            f"Relative energy drift Delta E / E0 = {e_drift:.3e} exceeded tolerance threshold "
                            f"({self.energy_drift_threshold:.1e}) in conservative unpowered orbit."
                        ),
                        "detection_rule": "|Delta E / E0| > threshold",
                        "observed_value": e_drift,
                        "reference_value": 0.0,
                        "residual": e_drift,
                        "threshold": self.energy_drift_threshold,
                        "status": "NEW",
                        "recommended_action": "Switch to Symplectic Velocity-Verlet or tighten Dormand-Prince rtol/atol."
                    })
                    break  # One finding per run is sufficient to avoid flooding

        # 4. Detector Family D: Propulsion & Propellant Depletion
        for evt in events:
            if evt.get("event_type") == "PROPELLANT_EXHAUSTED":
                findings.append({
                    "id": f"ANO-{uuid.uuid4().hex[:8].upper()}",
                    "time_sim": evt.get("time_sim", 0.0),
                    "experiment_id": experiment_id,
                    "model_id": model_id,
                    "category": "PROPULSION",
                    "severity": "WARNING",
                    "title": "Spacecraft Propellant Depleted",
                    "explanation": "Fuel mass reached 0.0 kg; subsequent maneuver commands will have zero effective thrust.",
                    "detection_rule": "propellant_mass <= 0.0",
                    "observed_value": 0.0,
                    "reference_value": "> 0.0 kg",
                    "residual": None,
                    "threshold": 0.0,
                    "status": "NEW",
                    "recommended_action": "Review mission delta-v budget or optimize burn duration schedule."
                })

        # 5. Detector Family E: Reference Model Disagreement
        if reference_result and trajectory:
            ref_traj = reference_result.get("trajectory", [])
            ref_model = reference_result.get("model_id", "REFERENCE")
            if ref_traj:
                max_dev = 0.0
                max_dev_time = 0.0
                # Compare overlapping time points
                n_pts = min(len(trajectory), len(ref_traj))
                for i in range(n_pts):
                    f1 = trajectory[i]
                    f2 = ref_traj[i]
                    p1 = np.array([f1["x"], f1["y"], f1["z"]])
                    p2 = np.array([f2["x"], f2["y"], f2["z"]])
                    dist = float(np.linalg.norm(p1 - p2))
                    if dist > max_dev:
                        max_dev = dist
                        max_dev_time = f1["t_sim"]

                if max_dev > self.max_position_residual_threshold:
                    findings.append({
                        "id": f"ANO-{uuid.uuid4().hex[:8].upper()}",
                        "time_sim": max_dev_time,
                        "experiment_id": experiment_id,
                        "model_id": model_id,
                        "category": "MODEL_DISAGREEMENT",
                        "severity": "INFO",
                        "title": f"Significant Trajectory Divergence vs {ref_model}",
                        "explanation": (
                            f"Maximum orbital displacement between {model_id} and {ref_model} reached {max_dev:.2f} m "
                            f"(threshold: {self.max_position_residual_threshold:.1f} m) at T+{max_dev_time:.1f} s."
                        ),
                        "detection_rule": "||r_model - r_ref|| > threshold",
                        "observed_value": max_dev,
                        "reference_value": 0.0,
                        "residual": max_dev,
                        "threshold": self.max_position_residual_threshold,
                        "status": "NEW",
                        "recommended_action": "Analyze whether divergence stems from kernel deformation or relativistic precession."
                    })

        return findings
