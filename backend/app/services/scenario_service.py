import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import ScenarioDefinition, ScenarioRunRecord
from app.schemas.scenario import ScenarioDefinitionCreate, ScenarioDefinitionResponse, ScenarioRunResponse
from app.services.simulation_engine import SimulationEngine
from app.schemas.state import SpacecraftMode

DEFAULT_SCENARIOS = [
    {
        "id": "SCN-NOMINAL",
        "name": "Nominal Flight Operations",
        "description": "Baseline orbital operations under nominal thermal and solar illumination conditions.",
        "seed": 42,
        "initial_config": {"duration_ticks": 30, "step_dt": 1.0},
        "fault_schedule": [],
        "expected_outcomes": {
            "final_mode": "NOMINAL",
            "max_temperature_c": 35.0,
            "min_battery_soc_pct": 80.0,
            "incidents_count": 0,
        },
        "version": "1.0.0",
    },
    {
        "id": "SCN-OVERHEAT-GRADUAL",
        "name": "Gradual Thermal Runaway",
        "description": "Thermal control subsystem loop degradation causing temperature to climb beyond the 75°C threshold.",
        "seed": 101,
        "initial_config": {"duration_ticks": 20, "step_dt": 1.0},
        "fault_schedule": [
            {"tick": 5, "fault_type": "OVERHEATING", "intensity": 3.0, "target_value": 78.5}
        ],
        "expected_outcomes": {
            "final_mode": "SAFE_MODE",
            "safe_mode_triggered": True,
            "fault_type_detected": "OVERHEATING",
        },
        "version": "1.0.0",
    },
    {
        "id": "SCN-OVERHEAT-SUDDEN",
        "name": "Sudden Avionics Thermal Spike",
        "description": "Rapid avionics sensor heating exceeding 82°C within two simulation steps.",
        "seed": 202,
        "initial_config": {"duration_ticks": 15, "step_dt": 1.0},
        "fault_schedule": [
            {"tick": 2, "fault_type": "OVERHEATING", "intensity": 8.0, "target_value": 84.0}
        ],
        "expected_outcomes": {
            "final_mode": "SAFE_MODE",
            "safe_mode_triggered": True,
            "fault_type_detected": "OVERHEATING",
        },
        "version": "1.0.0",
    },
    {
        "id": "SCN-COMM-LOSS",
        "name": "Ground Link Loss & Autonomous Hold",
        "description": "Ground station RF carrier loss. Demonstrates autonomous attitude hold and incident logging without premature safe mode.",
        "seed": 303,
        "initial_config": {"duration_ticks": 20, "step_dt": 1.0},
        "fault_schedule": [
            {"tick": 5, "fault_type": "COMM_LOSS", "intensity": 1.0}
        ],
        "expected_outcomes": {
            "comm_status": "LOST",
            "incident_created": "COMM_LOSS",
            "final_mode": "NOMINAL",
        },
        "version": "1.0.0",
    },
    {
        "id": "SCN-BATTERY-CRITICAL",
        "name": "Electrical Power Subsystem Depletion",
        "description": "Solar array drive mechanism failure during eclipse leading to bus under-voltage (<20% SOC).",
        "seed": 404,
        "initial_config": {"duration_ticks": 20, "step_dt": 1.0},
        "fault_schedule": [
            {"tick": 3, "fault_type": "LOW_BATTERY", "intensity": 4.0, "target_value": 16.5}
        ],
        "expected_outcomes": {
            "final_mode": "SAFE_MODE",
            "safe_mode_triggered": True,
            "fault_type_detected": "LOW_BATTERY_CRITICAL",
        },
        "version": "1.0.0",
    },
]

class ScenarioService:
    @staticmethod
    def seed_default_scenarios(db: Session) -> None:
        for sc in DEFAULT_SCENARIOS:
            existing = db.query(ScenarioDefinition).filter(ScenarioDefinition.id == sc["id"]).first()
            if not existing:
                record = ScenarioDefinition(
                    id=sc["id"],
                    name=sc["name"],
                    description=sc["description"],
                    seed=sc["seed"],
                    initial_config_json=json.dumps(sc["initial_config"]),
                    fault_schedule_json=json.dumps(sc["fault_schedule"]),
                    expected_outcomes_json=json.dumps(sc["expected_outcomes"]),
                    version=sc["version"],
                )
                db.add(record)
        db.commit()

    @staticmethod
    def get_scenarios(db: Session) -> List[ScenarioDefinition]:
        ScenarioService.seed_default_scenarios(db)
        return db.query(ScenarioDefinition).all()

    @staticmethod
    def get_scenario(db: Session, scenario_id: str) -> Optional[ScenarioDefinition]:
        return db.query(ScenarioDefinition).filter(ScenarioDefinition.id == scenario_id).first()

    @staticmethod
    def run_scenario(db: Session, scenario_id: str) -> ScenarioRunResponse:
        sc = ScenarioService.get_scenario(db, scenario_id)
        if not sc:
            raise ValueError(f"Scenario '{scenario_id}' not found.")

        run_id = f"SCN-RUN-{str(uuid.uuid4())[:8]}"
        initial_cfg = json.loads(sc.initial_config_json)
        fault_sched = json.loads(sc.fault_schedule_json)
        expected = json.loads(sc.expected_outcomes_json)

        # Isolated deterministic simulator instance
        sim = SimulationEngine()
        sim.start(db=db, name=f"Scenario:{sc.name}", seed=sc.seed, cadence_hz=1.0)

        duration_ticks = initial_cfg.get("duration_ticks", 20)
        step_dt = initial_cfg.get("step_dt", 1.0)

        max_temp = -999.0
        min_soc = 999.0
        safe_mode_triggered = False

        for tick in range(1, duration_ticks + 1):
            # Check fault schedule
            for fault in fault_sched:
                if fault.get("tick") == tick:
                    sim.inject_fault(
                        fault_type=fault["fault_type"],
                        intensity=fault.get("intensity", 1.0),
                        target_value=fault.get("target_value"),
                    )

            tel = sim.step(db=db, dt=step_dt)
            max_temp = max(max_temp, tel.get("temperature_c", 0.0))
            min_soc = min(min_soc, tel.get("battery_soc_pct", 100.0))
            if tel.get("mode") == SpacecraftMode.SAFE_MODE.value:
                safe_mode_triggered = True

        observed = {
            "final_mode": sim.current_mode.value,
            "max_temperature_c": round(max_temp, 2),
            "min_battery_soc_pct": round(min_soc, 2),
            "comm_status": sim.comm_status,
            "safe_mode_triggered": safe_mode_triggered,
        }

        # Check deviations from expected outcomes
        deviations = []
        if "final_mode" in expected and expected["final_mode"] != observed["final_mode"]:
            deviations.append(f"Expected final mode '{expected['final_mode']}', got '{observed['final_mode']}'")
        if "safe_mode_triggered" in expected and expected["safe_mode_triggered"] != observed["safe_mode_triggered"]:
            deviations.append(f"Expected safe_mode_triggered={expected['safe_mode_triggered']}, got {observed['safe_mode_triggered']}")
        if "comm_status" in expected and expected["comm_status"] != observed["comm_status"]:
            deviations.append(f"Expected comm_status '{expected['comm_status']}', got '{observed['comm_status']}'")

        pass_fail = "PASS" if len(deviations) == 0 else "FAIL"

        run_rec = ScenarioRunRecord(
            id=run_id,
            scenario_id=sc.id,
            run_id=sim.active_run_id,
            status="COMPLETED",
            seed=sc.seed,
            observed_outcomes_json=json.dumps(observed),
            pass_fail=pass_fail,
            deviations_json=json.dumps(deviations),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(run_rec)
        db.commit()

        return ScenarioRunResponse(
            id=run_id,
            scenario_id=sc.id,
            run_id=sim.active_run_id,
            status="COMPLETED",
            seed=sc.seed,
            observed_outcomes=observed,
            pass_fail=pass_fail,
            deviations=deviations,
            started_at=run_rec.started_at,
            completed_at=run_rec.completed_at,
        )
