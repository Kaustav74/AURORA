import pytest
from app.schemas.state import SpacecraftMode
from app.services.state_machine import StateMachine, StateMachineError

def test_permitted_transitions():
    # NOMINAL -> SAFE_MODE
    allowed, _ = StateMachine.is_transition_allowed(SpacecraftMode.NOMINAL, SpacecraftMode.SAFE_MODE)
    assert allowed is True

    # NOMINAL -> DEGRADED
    allowed, _ = StateMachine.is_transition_allowed(SpacecraftMode.NOMINAL, SpacecraftMode.DEGRADED)
    assert allowed is True

    # SAFE_MODE -> RECOVERY
    allowed, _ = StateMachine.is_transition_allowed(SpacecraftMode.SAFE_MODE, SpacecraftMode.RECOVERY)
    assert allowed is True

    # RECOVERY -> NOMINAL
    allowed, _ = StateMachine.is_transition_allowed(SpacecraftMode.RECOVERY, SpacecraftMode.NOMINAL)
    assert allowed is True

def test_rejected_transitions():
    # Direct SAFE_MODE -> NOMINAL is strictly forbidden
    allowed, msg = StateMachine.is_transition_allowed(SpacecraftMode.SAFE_MODE, SpacecraftMode.NOMINAL)
    assert allowed is False
    assert "strictly forbidden" in msg

    # Direct STANDBY -> SAFE_MODE
    allowed, _ = StateMachine.is_transition_allowed(SpacecraftMode.STANDBY, SpacecraftMode.SAFE_MODE)
    assert allowed is False

def test_recovery_preconditions_check():
    # Satisfied preconditions
    nominal_telemetry = {
        "temperature_c": 23.5,
        "battery_soc_pct": 85.0,
        "bus_voltage_v": 28.0,
        "comm_status": "NOMINAL",
    }
    ok, msg = StateMachine.check_recovery_preconditions(nominal_telemetry)
    assert ok is True

    # High temperature violation (>= 75.0 C)
    hot_telemetry = {
        "temperature_c": 76.2,
        "battery_soc_pct": 85.0,
        "bus_voltage_v": 28.0,
        "comm_status": "NOMINAL",
    }
    ok, msg = StateMachine.check_recovery_preconditions(hot_telemetry)
    assert ok is False
    assert "Temperature" in msg

    # Low battery violation (< 30.0%)
    drained_telemetry = {
        "temperature_c": 25.0,
        "battery_soc_pct": 22.0,
        "bus_voltage_v": 28.0,
        "comm_status": "NOMINAL",
    }
    ok, msg = StateMachine.check_recovery_preconditions(drained_telemetry)
    assert ok is False
    assert "Battery" in msg

    # Lost comm violation
    lost_comm_telemetry = {
        "temperature_c": 25.0,
        "battery_soc_pct": 85.0,
        "bus_voltage_v": 28.0,
        "comm_status": "LOST",
    }
    ok, msg = StateMachine.check_recovery_preconditions(lost_comm_telemetry)
    assert ok is False
    assert "communication link is LOST" in msg
