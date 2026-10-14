"""
AURORA Physics Lab - Service Layer
Orchestrates model creation, numerical orbit propagation, anomaly detection,
parameter fitting, model comparisons, and database persistence.
"""

from datetime import datetime, timezone
import json
import uuid
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session

from app.db import init_db
from app.db.models import (
    PhysicsExperimentRecord,
    PhysicsTrajectoryRecord,
    PhysicsAnomalyRecord,
)
from app.physics_lab.models.registry import PhysicsModelRegistry
from app.physics_lab.engine.propagator import OrbitPropagator
from app.physics_lab.engine.propulsion import PropulsionSubsystem
from app.physics_lab.analysis.anomaly_detector import AnomalyDetectorEngine
from app.physics_lab.analysis.parameter_fitter import ParameterFitterEngine
from app.schemas.physics_lab import (
    CreateExperimentRequest,
    CompareModelsRequest,
    ParameterSweepRequest,
    ParameterFitRequest,
)


class PhysicsLabService:
    @staticmethod
    def list_models() -> List[Dict[str, Any]]:
        return PhysicsModelRegistry.list_models()

    @staticmethod
    def get_model(model_id: str) -> Optional[Dict[str, Any]]:
        return PhysicsModelRegistry.get_model_metadata(model_id)

    @staticmethod
    def create_and_run_experiment(
        db: Session,
        request: CreateExperimentRequest,
    ) -> Dict[str, Any]:
        """
        Execute numerical orbit propagation and persist experiment, trajectory, and anomalies.
        """
        experiment_id = str(uuid.uuid4())

        # Instantiate physics model
        model = PhysicsModelRegistry.create_model_instance(
            model_id=request.model_id,
            parameters=request.model_parameters,
        )

        # Build propulsion subsystem if thrust or propellant is configured
        propulsion = None
        if request.thrust_n > 0.0 or request.propellant_mass_kg > 0.0:
            propulsion = PropulsionSubsystem(
                dry_mass=request.spacecraft_dry_mass_kg,
                propellant_mass=request.propellant_mass_kg,
                thrust_n=request.thrust_n,
                isp_seconds=request.isp_seconds,
                maneuvers=request.maneuvers,
            )

        # Build propagator
        propagator = OrbitPropagator(
            model=model,
            central_mass=request.central_mass_kg,
            integrator_name=request.integrator,
            rtol=request.rtol,
            atol=request.atol,
            propulsion=propulsion,
        )

        # Run simulation
        pos0 = np.array(request.initial_position_m, dtype=np.float64)
        vel0 = np.array(request.initial_velocity_mps, dtype=np.float64)

        sim_output = propagator.propagate(
            initial_position=pos0,
            initial_velocity=vel0,
            duration_seconds=request.duration_seconds,
            dt_initial=request.dt_initial,
            decimate_points=request.decimate_points,
        )

        # Run anomaly detection battery
        detector = AnomalyDetectorEngine()
        findings = detector.analyze_simulation_run(
            experiment_id=experiment_id,
            sim_result=sim_output,
        )

        # Ensure database tables exist
        init_db()

        # Persist experiment record
        cfg_dict = request.model_dump() if hasattr(request, "model_dump") else request.dict()
        exp_record = PhysicsExperimentRecord(
            id=experiment_id,
            name=request.name,
            model_id=request.model_id,
            model_version=model.model_version,
            central_mass_kg=request.central_mass_kg,
            status="COMPLETED",
            termination_reason=sim_output["termination_reason"],
            integrator=request.integrator,
            sim_duration_s=sim_output["sim_duration_s"],
            closest_approach_m=sim_output.get("closest_approach_m"),
            farthest_distance_m=sim_output.get("farthest_distance_m"),
            max_energy_drift=sim_output.get("max_energy_drift_rel"),
            config_json=json.dumps(cfg_dict),
            summary_json=json.dumps({
                "execution_duration_ms": sim_output["execution_duration_ms"],
                "total_steps": sim_output["total_steps"],
                "events_count": len(sim_output["events"]),
                "anomalies_count": len(findings),
                "schwarzschild_radius_m": sim_output["schwarzschild_radius_m"],
                "events": sim_output["events"],
            }),
            created_at=datetime.now(timezone.utc),
        )
        db.add(exp_record)

        # Persist decimated trajectory
        traj_record = PhysicsTrajectoryRecord(
            experiment_id=experiment_id,
            point_count=len(sim_output["trajectory"]),
            trajectory_json=json.dumps(sim_output["trajectory"]),
        )
        db.add(traj_record)

        # Persist anomalies
        for f in findings:
            ano_record = PhysicsAnomalyRecord(
                id=f["id"],
                experiment_id=experiment_id,
                time_sim=f["time_sim"],
                model_id=f["model_id"],
                category=f["category"],
                severity=f["severity"],
                title=f["title"],
                explanation=f["explanation"],
                detection_rule=f["detection_rule"],
                observed_value=str(f.get("observed_value") or ""),
                reference_value=str(f.get("reference_value") or ""),
                residual=f.get("residual"),
                threshold=str(f.get("threshold") or ""),
                status=f.get("status", "NEW"),
                recommended_action=f.get("recommended_action"),
                created_at=datetime.utcnow(),
            )
            db.add(ano_record)

        db.commit()

        # Build response
        res = dict(sim_output)
        res["experiment_id"] = experiment_id
        res["name"] = request.name
        res["anomalies"] = findings
        return res

    @staticmethod
    def get_experiment(db: Session, experiment_id: str) -> Optional[Dict[str, Any]]:
        record = db.query(PhysicsExperimentRecord).filter(PhysicsExperimentRecord.id == experiment_id).first()
        if not record:
            return None

        config = json.loads(record.config_json) if record.config_json else {}
        summary = json.loads(record.summary_json) if record.summary_json else {}

        # Fetch anomalies
        anomalies_records = (
            db.query(PhysicsAnomalyRecord)
            .filter(PhysicsAnomalyRecord.experiment_id == experiment_id)
            .order_by(PhysicsAnomalyRecord.time_sim.asc())
            .all()
        )
        anomalies = [
            {
                "id": a.id,
                "experiment_id": a.experiment_id,
                "time_sim": a.time_sim,
                "model_id": a.model_id,
                "category": a.category,
                "severity": a.severity,
                "title": a.title,
                "explanation": a.explanation,
                "detection_rule": a.detection_rule,
                "observed_value": a.observed_value,
                "reference_value": a.reference_value,
                "residual": a.residual,
                "threshold": a.threshold,
                "status": a.status,
                "recommended_action": a.recommended_action,
                "resolution_notes": a.resolution_notes,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in anomalies_records
        ]

        return {
            "id": record.id,
            "name": record.name,
            "model_id": record.model_id,
            "model_version": record.model_version,
            "central_mass_kg": record.central_mass_kg,
            "status": record.status,
            "termination_reason": record.termination_reason,
            "integrator": record.integrator,
            "sim_duration_s": record.sim_duration_s,
            "closest_approach_m": record.closest_approach_m,
            "farthest_distance_m": record.farthest_distance_m,
            "max_energy_drift": record.max_energy_drift,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "config": config,
            "summary": summary,
            "events": summary.get("events", []),
            "anomalies": anomalies,
        }

    @staticmethod
    def list_experiments(db: Session, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        records = (
            db.query(PhysicsExperimentRecord)
            .order_by(PhysicsExperimentRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "name": r.name,
                "model_id": r.model_id,
                "model_version": r.model_version,
                "central_mass_kg": r.central_mass_kg,
                "status": r.status,
                "termination_reason": r.termination_reason,
                "integrator": r.integrator,
                "sim_duration_s": r.sim_duration_s,
                "closest_approach_m": r.closest_approach_m,
                "farthest_distance_m": r.farthest_distance_m,
                "max_energy_drift": r.max_energy_drift,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]

    @staticmethod
    def get_trajectory(db: Session, experiment_id: str) -> Optional[Dict[str, Any]]:
        record = db.query(PhysicsTrajectoryRecord).filter(PhysicsTrajectoryRecord.experiment_id == experiment_id).first()
        if not record:
            return None
        points = json.loads(record.trajectory_json)
        exp = db.query(PhysicsExperimentRecord).filter(PhysicsExperimentRecord.id == experiment_id).first()
        model_id = exp.model_id if exp else "UNKNOWN"
        return {
            "experiment_id": experiment_id,
            "model_id": model_id,
            "point_count": record.point_count,
            "points": points,
        }

    @staticmethod
    def compare_models(db: Session, request: CompareModelsRequest) -> Dict[str, Any]:
        """
        Run side-by-side simulations of multiple models from identical initial conditions.
        """
        results_by_model: Dict[str, Any] = {}
        for m_id in request.model_ids:
            exp_req = CreateExperimentRequest(
                name=f"{request.name} ({m_id})",
                model_id=m_id,
                central_mass_kg=request.central_mass_kg,
                initial_position_m=request.initial_position_m,
                initial_velocity_mps=request.initial_velocity_mps,
                duration_seconds=request.duration_seconds,
                dt_initial=request.dt_initial,
                integrator=request.integrator,
                rtol=request.rtol,
                atol=request.atol,
                model_parameters=request.common_model_parameters,
                decimate_points=400,
            )
            sim_out = PhysicsLabService.create_and_run_experiment(db, exp_req)
            results_by_model[m_id] = sim_out

        # Pairwise differences against first model (baseline)
        base_id = request.model_ids[0]
        base_sim = results_by_model[base_id]
        base_traj = base_sim.get("trajectory", [])

        comparisons: List[Dict[str, Any]] = []
        for m_id in request.model_ids[1:]:
            comp_sim = results_by_model[m_id]
            comp_traj = comp_sim.get("trajectory", [])

            max_pos_delta = 0.0
            max_vel_delta = 0.0
            time_at_max = 0.0
            n_pts = min(len(base_traj), len(comp_traj))

            delta_series = []
            for i in range(n_pts):
                p1 = np.array([base_traj[i]["x"], base_traj[i]["y"], base_traj[i]["z"]])
                p2 = np.array([comp_traj[i]["x"], comp_traj[i]["y"], comp_traj[i]["z"]])
                v1 = np.array([base_traj[i]["vx"], base_traj[i]["vy"], base_traj[i]["vz"]])
                v2 = np.array([comp_traj[i]["vx"], comp_traj[i]["vy"], comp_traj[i]["vz"]])

                d_pos = float(np.linalg.norm(p1 - p2))
                d_vel = float(np.linalg.norm(v1 - v2))

                if d_pos > max_pos_delta:
                    max_pos_delta = d_pos
                    time_at_max = base_traj[i]["t_sim"]
                if d_vel > max_vel_delta:
                    max_vel_delta = d_vel

                delta_series.append({
                    "t_sim": base_traj[i]["t_sim"],
                    "pos_delta_m": round(d_pos, 2),
                    "vel_delta_mps": round(d_vel, 3),
                })

            comparisons.append({
                "baseline_model": base_id,
                "comparison_model": m_id,
                "max_position_delta_m": round(max_pos_delta, 2),
                "max_velocity_delta_mps": round(max_vel_delta, 3),
                "time_at_max_delta_s": time_at_max,
                "delta_series": delta_series[::max(1, len(delta_series) // 100)],
            })

        return {
            "name": request.name,
            "models_evaluated": request.model_ids,
            "individual_runs": results_by_model,
            "pairwise_comparisons": comparisons,
        }

    @staticmethod
    def get_anomalies(
        db: Session,
        experiment_id: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query = db.query(PhysicsAnomalyRecord)
        if experiment_id:
            query = query.filter(PhysicsAnomalyRecord.experiment_id == experiment_id)
        if category and category != "ALL":
            query = query.filter(PhysicsAnomalyRecord.category == category)
        if severity and severity != "ALL":
            query = query.filter(PhysicsAnomalyRecord.severity == severity)
        if status and status != "ALL":
            query = query.filter(PhysicsAnomalyRecord.status == status)

        records = query.order_by(PhysicsAnomalyRecord.created_at.desc()).offset(offset).limit(limit).all()
        return [
            {
                "id": a.id,
                "experiment_id": a.experiment_id,
                "time_sim": a.time_sim,
                "model_id": a.model_id,
                "category": a.category,
                "severity": a.severity,
                "title": a.title,
                "explanation": a.explanation,
                "detection_rule": a.detection_rule,
                "observed_value": a.observed_value,
                "reference_value": a.reference_value,
                "residual": a.residual,
                "threshold": a.threshold,
                "status": a.status,
                "recommended_action": a.recommended_action,
                "resolution_notes": a.resolution_notes,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in records
        ]

    @staticmethod
    def update_anomaly_status(
        db: Session,
        anomaly_id: str,
        status: str,
        resolution_notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        record = db.query(PhysicsAnomalyRecord).filter(PhysicsAnomalyRecord.id == anomaly_id).first()
        if not record:
            return None
        record.status = status
        if resolution_notes:
            record.resolution_notes = resolution_notes
        db.commit()
        return {
            "id": record.id,
            "status": record.status,
            "resolution_notes": record.resolution_notes,
        }

    @staticmethod
    def reproduce_anomaly(db: Session, anomaly_id: str) -> Optional[Dict[str, Any]]:
        """
        Re-run the exact configuration to reproduce the anomaly.
        """
        anomaly = db.query(PhysicsAnomalyRecord).filter(PhysicsAnomalyRecord.id == anomaly_id).first()
        if not anomaly:
            return None
        exp = db.query(PhysicsExperimentRecord).filter(PhysicsExperimentRecord.id == anomaly.experiment_id).first()
        if not exp or not exp.config_json:
            return None

        config_dict = json.loads(exp.config_json)
        req = CreateExperimentRequest(**config_dict)
        req.name = f"Reproduction of {anomaly.id}"

        reproduced_sim = PhysicsLabService.create_and_run_experiment(db, req)

        # Check if the anomaly was reproduced
        reproduced = any(a["category"] == anomaly.category for a in reproduced_sim["anomalies"])
        if reproduced:
            anomaly.status = "REPRODUCED"
            anomaly.resolution_notes = f"Reproduced in re-run {reproduced_sim['experiment_id']} at t={anomaly.time_sim:.1f} s."
            db.commit()

        return {
            "original_anomaly_id": anomaly.id,
            "is_reproduced": reproduced,
            "new_experiment_id": reproduced_sim["experiment_id"],
            "new_anomalies_count": len(reproduced_sim["anomalies"]),
        }

    @staticmethod
    def diagnostic_rerun(db: Session, anomaly_id: str) -> Optional[Dict[str, Any]]:
        """
        Execute high-accuracy diagnostic run with 10x tighter tolerances.
        """
        anomaly = db.query(PhysicsAnomalyRecord).filter(PhysicsAnomalyRecord.id == anomaly_id).first()
        if not anomaly:
            return None
        exp = db.query(PhysicsExperimentRecord).filter(PhysicsExperimentRecord.id == anomaly.experiment_id).first()
        if not exp or not exp.config_json:
            return None

        config_dict = json.loads(exp.config_json)
        req = CreateExperimentRequest(**config_dict)
        req.name = f"Diagnostic Rerun for {anomaly.id}"
        req.rtol = max(1.0e-10, req.rtol * 0.1)
        req.atol = max(1.0e-12, req.atol * 0.1)
        req.dt_initial = max(0.5, req.dt_initial * 0.2)

        diagnostic_sim = PhysicsLabService.create_and_run_experiment(db, req)

        return {
            "original_anomaly_id": anomaly.id,
            "diagnostic_experiment_id": diagnostic_sim["experiment_id"],
            "tighter_rtol": req.rtol,
            "tighter_atol": req.atol,
            "anomalies_detected": diagnostic_sim["anomalies"],
        }

    @staticmethod
    def run_sweep(request: ParameterSweepRequest) -> Dict[str, Any]:
        return ParameterFitterEngine.run_parameter_sweep(
            model_id=request.model_id,
            param_name=request.param_name,
            param_values=request.param_values,
            base_parameters=request.base_parameters or {},
            initial_position=request.initial_position_m,
            initial_velocity=request.initial_velocity_mps,
            central_mass=request.central_mass_kg,
            duration_seconds=request.duration_seconds,
        )

    @staticmethod
    def run_fit(request: ParameterFitRequest) -> Dict[str, Any]:
        if len(request.bounds) != 2:
            raise ValueError("Bounds must contain [min, max]")
        return ParameterFitterEngine.fit_single_parameter(
            model_id=request.model_id,
            param_to_fit=request.param_to_fit,
            initial_guess=request.initial_guess,
            bounds=(request.bounds[0], request.bounds[1]),
            target_radial_speeds=request.target_radial_speeds,
            central_mass=request.central_mass_kg,
            base_parameters=request.base_parameters,
        )
