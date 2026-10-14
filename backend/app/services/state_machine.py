from datetime import datetime
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from app.schemas.state import SpacecraftMode
from app.db.models import SpacecraftStateRecord, EventRecord
from app.core.config import settings

# Explicit Permitted Transitions Table
# Key: source mode, Value: set of allowed destination modes
ALLOWED_TRANSITIONS = {
    SpacecraftMode.STANDBY: {
        SpacecraftMode.NOMINAL,
        SpacecraftMode.SIMULATION_STOPPED,
    },
    SpacecraftMode.NOMINAL: {
        SpacecraftMode.DEGRADED,
        SpacecraftMode.SAFE_MODE,
        SpacecraftMode.STANDBY,
        SpacecraftMode.SIMULATION_STOPPED,
    },
    SpacecraftMode.DEGRADED: {
        SpacecraftMode.NOMINAL,
        SpacecraftMode.SAFE_MODE,
        SpacecraftMode.STANDBY,
        SpacecraftMode.SIMULATION_STOPPED,
    },
    SpacecraftMode.SAFE_MODE: {
        SpacecraftMode.RECOVERY,
        SpacecraftMode.SIMULATION_STOPPED,
    },
    SpacecraftMode.RECOVERY: {
        SpacecraftMode.NOMINAL,
        SpacecraftMode.DEGRADED,
        SpacecraftMode.SAFE_MODE,
        SpacecraftMode.SIMULATION_STOPPED,
    },
    SpacecraftMode.SIMULATION_STOPPED: {
        SpacecraftMode.STANDBY,
    },
}

class StateMachineError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass

class StateMachine:
    @staticmethod
    def is_transition_allowed(current_mode: SpacecraftMode, target_mode: SpacecraftMode) -> Tuple[bool, str]:
        if current_mode == target_mode:
            return True, f"Already in mode {target_mode.value}"
        
        allowed_targets = ALLOWED_TRANSITIONS.get(current_mode, set())
        if target_mode in allowed_targets:
            return True, f"Transition from {current_mode.value} to {target_mode.value} is permitted."
        
        # Explicit error explanations for restricted transitions
        if current_mode == SpacecraftMode.SAFE_MODE and target_mode == SpacecraftMode.NOMINAL:
            return False, "Direct transition from SAFE_MODE to NOMINAL is strictly forbidden. Spacecraft must enter RECOVERY with verified preconditions first."
        
        return False, f"Illegal state transition from {current_mode.value} to {target_mode.value} according to flight operations rules."

    @staticmethod
    def check_recovery_preconditions(
        telemetry: Optional[dict] = None,
        unresolved_critical_incidents: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """
        Verify all operational preconditions before permitting SAFE_MODE -> RECOVERY transition.
        Preconditions:
        1. Temperature < OVERHEAT_THRESHOLD_C (75.0°C)
        2. Battery SOC >= 30.0%
        3. Bus Voltage >= 26.0 V
        4. Comm status is not LOST
        5. Zero open unacknowledged critical incidents
        """
        if telemetry is None:
            return False, "Cannot verify recovery: No telemetry data available."
        
        temp = telemetry.get("temperature_c", 0.0)
        if temp >= settings.OVERHEAT_THRESHOLD_C:
            return False, f"Recovery Precondition Failed: Temperature ({temp:.1f}°C) exceeds safety limit ({settings.OVERHEAT_THRESHOLD_C}°C)."

        soc = telemetry.get("battery_soc_pct", 0.0)
        if soc < 30.0:
            return False, f"Recovery Precondition Failed: Battery state of charge ({soc:.1f}%) is below recovery minimum (30.0%)."

        voltage = telemetry.get("bus_voltage_v", 0.0)
        if voltage < 26.0:
            return False, f"Recovery Precondition Failed: Bus voltage ({voltage:.2f}V) is below recovery threshold (26.0V)."

        comm = telemetry.get("comm_status", "LOST")
        if comm == "LOST":
            return False, "Recovery Precondition Failed: Spacecraft communication link is LOST. Ground uplink required."

        if unresolved_critical_incidents and len(unresolved_critical_incidents) > 0:
            incident_list = ", ".join(unresolved_critical_incidents)
            return False, f"Recovery Precondition Failed: Unresolved critical incidents active: [{incident_list}]."

        return True, "All recovery preconditions satisfied: thermal, electrical, and link parameters nominal."

    @staticmethod
    def transition(
        db: Session,
        run_id: str,
        current_mode: SpacecraftMode,
        target_mode: SpacecraftMode,
        reason: str,
        source: str,
        sim_time: float,
    ) -> SpacecraftStateRecord:
        allowed, msg = StateMachine.is_transition_allowed(current_mode, target_mode)
        if not allowed:
            raise StateMachineError(msg)

        state_rec = SpacecraftStateRecord(
            run_id=run_id,
            mode=target_mode.value,
            previous_mode=current_mode.value,
            reason=reason,
            source=source,
            timestamp_sim=sim_time,
            timestamp_wall=datetime.utcnow(),
        )
        db.add(state_rec)

        event = EventRecord(
            id=f"EVT-ST-{int(sim_time * 1000)}-{target_mode.value[:3]}",
            run_id=run_id,
            event_type="STATE_TRANSITION",
            category="OPERATIONS",
            severity="CRITICAL" if target_mode == SpacecraftMode.SAFE_MODE else "INFO",
            message=f"Spacecraft mode transitioned from {current_mode.value} to {target_mode.value}: {reason}",
            details_json=f'{{"previous_mode": "{current_mode.value}", "target_mode": "{target_mode.value}", "source": "{source}"}}',
            timestamp_sim=sim_time,
            timestamp_wall=datetime.utcnow(),
        )
        db.add(event)
        db.commit()
        db.refresh(state_rec)
        return state_rec
