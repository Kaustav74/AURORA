import math
import random
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models import SimulationRun, SpacecraftStateRecord, TelemetryRecord, EventRecord
from app.schemas.state import SpacecraftMode
from app.schemas.simulation import SimulationStatus
from app.services.state_machine import StateMachine, StateMachineError
from app.services.fault_engine import FaultEngine
from app.core.config import settings
from app.core.logging import logger

class SimulationEngine:
    def __init__(self):
        self.active_run_id: Optional[str] = None
        self.name: str = "AURORA-1 Baseline"
        self.status: SimulationStatus = SimulationStatus.STOPPED
        self.seed: int = 42
        self.cadence_hz: float = settings.DEFAULT_SIMULATION_CADENCE_HZ
        self.sim_time_seconds: float = 0.0
        self.start_wall_time: Optional[datetime] = None
        self.current_mode: SpacecraftMode = SpacecraftMode.STANDBY
        self._rng = random.Random(42)

        # Telemetry State variables
        self.temperature_c: float = 24.5
        self.battery_soc_pct: float = 95.0
        self.bus_voltage_v: float = 28.2
        self.current_draw_a: float = 3.4
        self.comm_status: str = "NOMINAL"
        self.signal_quality_pct: float = 98.0
        self.attitude_error_deg: float = 0.12
        self.angular_rate_deg_s: float = 0.015
        self.storage_used_pct: float = 35.0
        self.sensors_valid: bool = True

        # Injected faults table: fault_type -> { "target_value": ..., "remaining_seconds": ..., "active": bool }
        self.active_faults: Dict[str, Dict[str, Any]] = {}

        # Cache of most recent generated telemetry frame
        self.latest_telemetry: Optional[Dict[str, Any]] = None

    def start(self, db: Session, name: str = "Mission Alpha", seed: int = 42, cadence_hz: float = 1.0, config: Optional[Dict[str, Any]] = None) -> SimulationRun:
        if self.status == SimulationStatus.RUNNING:
            self.stop(db)

        self.active_run_id = str(uuid.uuid4())
        self.name = name
        self.seed = seed
        self.cadence_hz = cadence_hz
        self.sim_time_seconds = 0.0
        self.start_wall_time = datetime.utcnow()
        self.status = SimulationStatus.RUNNING
        self._rng = random.Random(seed)
        self.active_faults.clear()

        # Initial Subsystem parameters
        self.temperature_c = 24.5
        self.battery_soc_pct = 95.0
        self.bus_voltage_v = 28.2
        self.current_draw_a = 3.4
        self.comm_status = "NOMINAL"
        self.signal_quality_pct = 98.0
        self.attitude_error_deg = 0.12
        self.angular_rate_deg_s = 0.015
        self.storage_used_pct = 35.0
        self.sensors_valid = True

        # Persist SimulationRun in SQLite
        sim_run = SimulationRun(
            id=self.active_run_id,
            name=self.name,
            status=self.status.value,
            seed=self.seed,
            cadence_hz=self.cadence_hz,
            sim_time_seconds=0.0,
            start_wall_time=self.start_wall_time,
            updated_wall_time=self.start_wall_time,
            config_json=json.dumps(config or {}),
        )
        db.add(sim_run)

        # Initial State: Transition from STANDBY to NOMINAL
        self.current_mode = SpacecraftMode.NOMINAL
        state_rec = SpacecraftStateRecord(
            run_id=self.active_run_id,
            mode=SpacecraftMode.NOMINAL.value,
            previous_mode=SpacecraftMode.STANDBY.value,
            reason="Mission initialization sequence complete. All subsystems reported green.",
            source="SIMULATION_ENGINE",
            timestamp_sim=0.0,
            timestamp_wall=self.start_wall_time,
        )
        db.add(state_rec)

        event = EventRecord(
            id=f"EVT-START-{self.active_run_id[:8]}",
            run_id=self.active_run_id,
            event_type="SIM_LIFECYCLE",
            category="SYSTEM",
            severity="INFO",
            message=f"Simulation run '{self.name}' started with seed {self.seed}.",
            details_json=json.dumps({"run_id": self.active_run_id, "seed": self.seed}),
            timestamp_sim=0.0,
            timestamp_wall=self.start_wall_time,
        )
        db.add(event)

        db.commit()

        # Generate initial telemetry point
        self.step(db=db, dt=0.0)
        return sim_run

    def pause(self, db: Session) -> None:
        if self.status != SimulationStatus.RUNNING:
            raise ValueError(f"Cannot pause simulation in state {self.status.value}.")
        self.status = SimulationStatus.PAUSED
        if self.active_run_id:
            sim_run = db.query(SimulationRun).filter(SimulationRun.id == self.active_run_id).first()
            if sim_run:
                sim_run.status = SimulationStatus.PAUSED.value
                sim_run.updated_wall_time = datetime.utcnow()
                db.commit()

    def resume(self, db: Session) -> None:
        if self.status != SimulationStatus.PAUSED:
            raise ValueError(f"Cannot resume simulation in state {self.status.value}.")
        self.status = SimulationStatus.RUNNING
        if self.active_run_id:
            sim_run = db.query(SimulationRun).filter(SimulationRun.id == self.active_run_id).first()
            if sim_run:
                sim_run.status = SimulationStatus.RUNNING.value
                sim_run.updated_wall_time = datetime.utcnow()
                db.commit()

    def stop(self, db: Session) -> None:
        if self.status == SimulationStatus.STOPPED:
            return
        old_status = self.status
        self.status = SimulationStatus.STOPPED
        if self.active_run_id:
            sim_run = db.query(SimulationRun).filter(SimulationRun.id == self.active_run_id).first()
            if sim_run:
                sim_run.status = SimulationStatus.STOPPED.value
                sim_run.updated_wall_time = datetime.utcnow()
                db.commit()

            # Record stop state and event
            prev_mode = self.current_mode
            self.current_mode = SpacecraftMode.SIMULATION_STOPPED
            state_rec = SpacecraftStateRecord(
                run_id=self.active_run_id,
                mode=SpacecraftMode.SIMULATION_STOPPED.value,
                previous_mode=prev_mode.value,
                reason="Operator commanded simulation stop.",
                source="OPERATOR_LIFECYCLE",
                timestamp_sim=self.sim_time_seconds,
                timestamp_wall=datetime.utcnow(),
            )
            db.add(state_rec)

            event = EventRecord(
                id=f"EVT-STOP-{self.active_run_id[:8]}",
                run_id=self.active_run_id,
                event_type="SIM_LIFECYCLE",
                category="SYSTEM",
                severity="INFO",
                message=f"Simulation run '{self.name}' stopped at sim_time={self.sim_time_seconds:.1f}s.",
                details_json=json.dumps({"run_id": self.active_run_id, "sim_time": self.sim_time_seconds}),
                timestamp_sim=self.sim_time_seconds,
                timestamp_wall=datetime.utcnow(),
            )
            db.add(event)
            db.commit()

    def inject_fault(self, fault_type: str, intensity: float = 1.0, duration_seconds: Optional[float] = None, target_value: Optional[float] = None) -> None:
        self.active_faults[fault_type] = {
            "intensity": intensity,
            "remaining_seconds": duration_seconds,
            "target_value": target_value,
            "active": True,
        }
        logger.info(f"Fault injected: {fault_type} (intensity={intensity}, target={target_value})")

    def clear_fault(self, fault_type: str) -> None:
        if fault_type in self.active_faults:
            del self.active_faults[fault_type]
            logger.info(f"Fault cleared: {fault_type}")

    def step(self, db: Session, dt: float = 1.0) -> Dict[str, Any]:
        """
        Advance simulation time deterministically by dt seconds.
        Generates plausible telemetry, runs fault engine, and handles automated transitions.
        """
        if self.status != SimulationStatus.RUNNING and dt > 0:
            return self.latest_telemetry or {}

        if not self.active_run_id:
            # Generate a temporary run id if stepped without explicit start (e.g. initial dev state)
            self.start(db=db, name="Aurora Auto-Run", seed=self.seed)

        self.sim_time_seconds += dt

        # Update remaining duration of active faults
        faults_to_remove = []
        for ftype, fdata in self.active_faults.items():
            if fdata.get("remaining_seconds") is not None:
                fdata["remaining_seconds"] -= dt
                if fdata["remaining_seconds"] <= 0:
                    faults_to_remove.append(ftype)
        for ftype in faults_to_remove:
            del self.active_faults[ftype]

        # -----------------------------------------------------------------
        # Physics / Subsystem Simulation Models (Educational / Fictional)
        # -----------------------------------------------------------------
        noise = (self._rng.random() - 0.5) * 0.1

        # 1. Thermal Subsystem
        # Orbital day/night cycle: 90 minute simulated period (5400s)
        orbit_phase = (self.sim_time_seconds % 5400) / 5400.0 * 2.0 * math.pi
        sunlight = max(0.0, math.sin(orbit_phase))

        if "OVERHEATING" in self.active_faults:
            overheat = self.active_faults["OVERHEATING"]
            target = overheat.get("target_value")
            if target is not None:
                # Approach target rapidly
                self.temperature_c += (target - self.temperature_c) * 0.4
            else:
                self.temperature_c += 4.5 * overheat.get("intensity", 1.0)
        else:
            if self.current_mode == SpacecraftMode.SAFE_MODE:
                # In safe mode, non-essential heaters and payload are off, cooling down
                self.temperature_c += (18.0 - self.temperature_c) * 0.05 + noise
            else:
                base_temp = 22.0 + 6.0 * sunlight
                self.temperature_c += (base_temp - self.temperature_c) * 0.08 + noise

        # 2. Electrical Power Subsystem (EPS)
        if "LOW_BATTERY" in self.active_faults:
            lb = self.active_faults["LOW_BATTERY"]
            target = lb.get("target_value")
            if target is not None:
                self.battery_soc_pct += (target - self.battery_soc_pct) * 0.3
            else:
                self.battery_soc_pct = max(5.0, self.battery_soc_pct - 2.5 * lb.get("intensity", 1.0))
        else:
            if self.current_mode == SpacecraftMode.SAFE_MODE:
                # Load shed: current draw drops to 1.1A
                self.current_draw_a = 1.1 + abs(noise) * 0.1
                # Solar recharge in sunlight, minimal drain in shadow
                delta_soc = (0.2 if sunlight > 0.3 else -0.05) * dt
                self.battery_soc_pct = min(100.0, max(15.0, self.battery_soc_pct + delta_soc))
            elif self.current_mode == SpacecraftMode.DEGRADED:
                self.current_draw_a = 2.2 + abs(noise) * 0.2
                delta_soc = (0.1 if sunlight > 0.4 else -0.1) * dt
                self.battery_soc_pct = min(100.0, max(15.0, self.battery_soc_pct + delta_soc))
            else:
                self.current_draw_a = 3.5 + abs(noise) * 0.3
                delta_soc = (0.15 if sunlight > 0.3 else -0.12) * dt
                self.battery_soc_pct = min(100.0, max(20.0, self.battery_soc_pct + delta_soc))

        # Bus voltage modeled with battery SoC curve
        self.bus_voltage_v = 24.0 + 4.2 * (self.battery_soc_pct / 100.0) + (self._rng.random() - 0.5) * 0.05

        # 3. Communications Subsystem
        if "COMM_LOSS" in self.active_faults:
            self.comm_status = "LOST"
            self.signal_quality_pct = 0.0
        elif "COMM_DEGRADED" in self.active_faults:
            self.comm_status = "DEGRADED"
            self.signal_quality_pct = max(10.0, 45.0 + noise * 5.0)
        else:
            self.comm_status = "NOMINAL"
            self.signal_quality_pct = min(100.0, max(85.0, 97.5 + noise * 2.0))

        # 4. ADCS (Attitude Determination and Control)
        if "ATTITUDE_ERROR" in self.active_faults:
            self.attitude_error_deg = self.active_faults["ATTITUDE_ERROR"].get("target_value", 18.5)
            self.angular_rate_deg_s = 0.25
        else:
            if self.current_mode == SpacecraftMode.SAFE_MODE:
                # Sun-safe pointing mode: low error relative to sun line
                self.attitude_error_deg = max(0.05, 0.45 + noise)
                self.angular_rate_deg_s = 0.008
            else:
                self.attitude_error_deg = max(0.01, 0.15 + noise)
                self.angular_rate_deg_s = max(0.001, 0.015 + noise * 0.05)

        # 5. Onboard Data Handling (OBDH)
        if "STORAGE_FULL" in self.active_faults:
            self.storage_used_pct = self.active_faults["STORAGE_FULL"].get("target_value", 94.5)
        else:
            self.storage_used_pct = min(99.0, self.storage_used_pct + 0.005 * dt)

        # 6. Sensors Validity
        if "SENSOR_FAULT" in self.active_faults:
            self.sensors_valid = False
        else:
            self.sensors_valid = True

        # Assemble telemetry frame
        telemetry_data = {
            "run_id": self.active_run_id,
            "timestamp_sim": round(self.sim_time_seconds, 2),
            "timestamp_wall": datetime.utcnow().isoformat(),
            "mode": self.current_mode.value,
            "temperature_c": round(self.temperature_c, 2),
            "battery_soc_pct": round(self.battery_soc_pct, 2),
            "bus_voltage_v": round(self.bus_voltage_v, 2),
            "current_draw_a": round(self.current_draw_a, 2),
            "comm_status": self.comm_status,
            "signal_quality_pct": round(self.signal_quality_pct, 1),
            "attitude_error_deg": round(self.attitude_error_deg, 3),
            "angular_rate_deg_s": round(self.angular_rate_deg_s, 4),
            "storage_used_pct": round(self.storage_used_pct, 2),
            "sensors_valid": self.sensors_valid,
            "metadata": {
                "sunlight_factor": round(sunlight, 3),
                "active_faults": list(self.active_faults.keys()),
            },
        }
        self.latest_telemetry = telemetry_data

        # Persist TelemetryRecord in database
        tel_rec = TelemetryRecord(
            run_id=self.active_run_id,
            timestamp_sim=self.sim_time_seconds,
            timestamp_wall=datetime.utcnow(),
            mode=self.current_mode.value,
            temperature_c=self.temperature_c,
            battery_soc_pct=self.battery_soc_pct,
            bus_voltage_v=self.bus_voltage_v,
            current_draw_a=self.current_draw_a,
            comm_status=self.comm_status,
            signal_quality_pct=self.signal_quality_pct,
            attitude_error_deg=self.attitude_error_deg,
            angular_rate_deg_s=self.angular_rate_deg_s,
            storage_used_pct=self.storage_used_pct,
            sensors_valid=self.sensors_valid,
            metadata_json=json.dumps(telemetry_data["metadata"]),
        )
        db.add(tel_rec)

        # Update run sim_time in database
        sim_run = db.query(SimulationRun).filter(SimulationRun.id == self.active_run_id).first()
        if sim_run:
            sim_run.sim_time_seconds = self.sim_time_seconds
            sim_run.updated_wall_time = datetime.utcnow()

        db.commit()

        # Run Rule-Based Fault Detection
        fault_eval = FaultEngine.evaluate(
            db=db,
            run_id=self.active_run_id,
            telemetry=telemetry_data,
            current_mode=self.current_mode,
            sim_time=self.sim_time_seconds,
        )

        # Trigger SAFE_MODE if critical fault detected and not already safe
        if fault_eval.should_trigger_safe_mode:
            if self.current_mode != SpacecraftMode.SAFE_MODE:
                logger.warning(f"Critical fault triggered SAFE_MODE: {fault_eval.safe_mode_reason}")
                try:
                    StateMachine.transition(
                        db=db,
                        run_id=self.active_run_id,
                        current_mode=self.current_mode,
                        target_mode=SpacecraftMode.SAFE_MODE,
                        reason=fault_eval.safe_mode_reason or "Automated autonomous safe hold triggered by fault engine.",
                        source="FAULT_DETECTION_ENGINE",
                        sim_time=self.sim_time_seconds,
                    )
                    self.current_mode = SpacecraftMode.SAFE_MODE
                    telemetry_data["mode"] = SpacecraftMode.SAFE_MODE.value
                except StateMachineError as sme:
                    logger.error(f"Failed to transition to SAFE_MODE: {sme}")

        return telemetry_data

# Global Singleton Simulation Instance for the Backend Process
simulator = SimulationEngine()
