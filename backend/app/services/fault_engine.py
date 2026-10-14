import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models import IncidentRecord, EventRecord
from app.schemas.state import SpacecraftMode
from app.schemas.incident import IncidentSeverity, IncidentStatus
from app.core.config import settings

class FaultDetectionResult:
    def __init__(self):
        self.new_incidents: List[IncidentRecord] = []
        self.updated_incidents: List[IncidentRecord] = []
        self.should_trigger_safe_mode: bool = False
        self.safe_mode_reason: Optional[str] = None
        self.warnings: List[str] = []

class FaultEngine:
    @staticmethod
    def evaluate(
        db: Session,
        run_id: str,
        telemetry: Dict[str, Any],
        current_mode: SpacecraftMode,
        sim_time: float,
    ) -> FaultDetectionResult:
        result = FaultDetectionResult()

        temp = float(telemetry.get("temperature_c", 25.0))
        battery = float(telemetry.get("battery_soc_pct", 100.0))
        voltage = float(telemetry.get("bus_voltage_v", 28.0))
        comm = str(telemetry.get("comm_status", "NOMINAL"))
        attitude_err = float(telemetry.get("attitude_error_deg", 0.0))
        storage = float(telemetry.get("storage_used_pct", 10.0))
        sensors_valid = bool(telemetry.get("sensors_valid", True))

        # Helper to find or create incident
        def handle_incident(
            fault_type: str,
            severity: IncidentSeverity,
            summary: str,
            details: str,
            trigger_safe_mode: bool = False,
        ):
            # Check existing open or acknowledged incident
            existing = (
                db.query(IncidentRecord)
                .filter(
                    IncidentRecord.run_id == run_id,
                    IncidentRecord.fault_type == fault_type,
                    IncidentRecord.status.in_([IncidentStatus.OPEN.value, IncidentStatus.ACKNOWLEDGED.value]),
                )
                .first()
            )

            if existing:
                existing.last_seen_sim = sim_time
                existing.telemetry_snapshot_json = json.dumps(telemetry)
                result.updated_incidents.append(existing)
            else:
                inc_id = f"INC-{fault_type}-{int(sim_time)}"
                incident = IncidentRecord(
                    id=inc_id,
                    run_id=run_id,
                    fault_type=fault_type,
                    severity=severity.value,
                    status=IncidentStatus.OPEN.value,
                    summary=summary,
                    details=details,
                    first_seen_sim=sim_time,
                    last_seen_sim=sim_time,
                    telemetry_snapshot_json=json.dumps(telemetry),
                )
                db.add(incident)
                result.new_incidents.append(incident)

                # Persist event
                evt = EventRecord(
                    id=f"EVT-FLT-{int(sim_time * 1000)}-{fault_type[:3]}",
                    run_id=run_id,
                    event_type="FAULT_DETECTED",
                    category="FAULT",
                    severity=severity.value,
                    message=f"Fault detected: {summary}",
                    details_json=json.dumps({"fault_type": fault_type, "details": details}),
                    timestamp_sim=sim_time,
                    timestamp_wall=datetime.utcnow(),
                )
                db.add(evt)

            if trigger_safe_mode:
                result.should_trigger_safe_mode = True
                result.safe_mode_reason = f"{fault_type}: {summary}"

        # RULE 1: Thermal Overheating (> 75.0°C fictional threshold)
        if temp >= settings.OVERHEAT_THRESHOLD_C:
            handle_incident(
                fault_type="OVERHEATING",
                severity=IncidentSeverity.CRITICAL,
                summary=f"Thermal threshold exceeded ({temp:.1f}°C >= {settings.OVERHEAT_THRESHOLD_C}°C)",
                details=f"Core avionics package temperature is {temp:.2f}°C, exceeding maximum allowable limit of {settings.OVERHEAT_THRESHOLD_C}°C. Immediate safe hold required.",
                trigger_safe_mode=(current_mode not in (SpacecraftMode.SAFE_MODE, SpacecraftMode.SIMULATION_STOPPED)),
            )

        # RULE 2: Power Depletion / Bus Under-Voltage
        if battery < 20.0 or voltage < 22.0:
            handle_incident(
                fault_type="LOW_BATTERY_CRITICAL",
                severity=IncidentSeverity.CRITICAL,
                summary=f"Critical Power Degradation (SoC: {battery:.1f}%, Bus: {voltage:.2f}V)",
                details=f"Battery state of charge has dropped to {battery:.1f}% (< 20%) or bus voltage dropped to {voltage:.2f}V (< 22.0V). Non-essential loads must be shed.",
                trigger_safe_mode=(current_mode not in (SpacecraftMode.SAFE_MODE, SpacecraftMode.SIMULATION_STOPPED)),
            )
        elif battery < 35.0:
            handle_incident(
                fault_type="BATTERY_WARNING",
                severity=IncidentSeverity.WARNING,
                summary=f"Battery reserve caution (SoC: {battery:.1f}%)",
                details=f"Battery state of charge is below 35.0%. Power balance requires monitoring.",
                trigger_safe_mode=False,
            )

        # RULE 3: Communication Loss
        if comm == "LOST":
            handle_incident(
                fault_type="COMM_LOSS",
                severity=IncidentSeverity.WARNING,
                summary="Ground RF Carrier Loss",
                details="Downlink / uplink signal lost. Autonomous attitude hold and watchdog timer engaged.",
                trigger_safe_mode=False,
            )

        # RULE 4: Sensor Validity / Disagreement
        if not sensors_valid:
            handle_incident(
                fault_type="SENSOR_INVALID",
                severity=IncidentSeverity.WARNING,
                summary="Telemetry sensor sanity check failed",
                details="Sensors flagged invalid or payload parity error detected.",
                trigger_safe_mode=False,
            )

        # RULE 5: Attitude Pointing Error
        if attitude_err > 15.0:
            handle_incident(
                fault_type="ATTITUDE_DISAGREEMENT",
                severity=IncidentSeverity.WARNING,
                summary=f"ADCS pointing error excessive ({attitude_err:.2f}° > 15.0°)",
                details=f"Spacecraft body attitude error is {attitude_err:.2f} degrees. ADCS reaction wheels saturation or sun sensor dropout.",
                trigger_safe_mode=False,
            )

        # RULE 6: Mass Memory Storage Pressure
        if storage > 90.0:
            handle_incident(
                fault_type="STORAGE_PRESSURE",
                severity=IncidentSeverity.WARNING,
                summary=f"Onboard storage capacity critical ({storage:.1f}% > 90%)",
                details=f"Solid-State Recorder (SSR) buffer utilized at {storage:.1f}%. Risk of telemetry frame overwrite if downlink pass is missed.",
                trigger_safe_mode=False,
            )

        db.commit()
        return result
