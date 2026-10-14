import pytest
from app.schemas.state import SpacecraftMode
from app.db.models import SpacecraftStateRecord, EventRecord, IncidentRecord
from app.services.simulation_engine import simulator
from app.services.state_machine import StateMachine

def test_first_vertical_slice_overheating_and_safe_mode(client, db_session):
    # 1. Start clean simulation run
    start_resp = client.post("/api/v1/simulation/start", json={"name": "Vertical Slice Test", "seed": 42})
    assert start_resp.status_code == 200
    run_id = start_resp.json()["run_id"]
    assert run_id is not None

    # 2. Verify current telemetry is nominal and in NOMINAL mode
    tel_resp = client.get("/api/v1/telemetry/current")
    assert tel_resp.status_code == 200
    data = tel_resp.json()
    assert data["mode"] == "NOMINAL"
    assert data["temperature_c"] < 75.0
    assert 0.0 <= data["battery_soc_pct"] <= 100.0
    assert data["bus_voltage_v"] > 20.0

    # 3. Verify fault injection endpoint is forbidden when disabled
    inj_resp = client.post("/api/v1/faults/inject", json={"fault_type": "OVERHEATING", "target_value": 80.0})
    assert inj_resp.status_code == 403
    assert "Development/test fault injection is disabled" in inj_resp.json()["detail"]

    # 4. Inject overheating fault directly into engine
    simulator.inject_fault("OVERHEATING", intensity=5.0, target_value=82.0)

    # 5. Advance simulation steps until temperature crosses threshold
    stepped_data = None
    for _ in range(10):
        step_resp = client.post("/api/v1/simulation/step?dt=1.0")
        assert step_resp.status_code == 200
        stepped_data = step_resp.json()["telemetry"]
        if stepped_data["temperature_c"] >= 75.0:
            break

    # 6. Verify temperature crossed 75.0°C and mode transitioned to SAFE_MODE
    assert stepped_data["temperature_c"] >= 75.0
    assert simulator.current_mode == SpacecraftMode.SAFE_MODE
    assert stepped_data["mode"] == "SAFE_MODE"

    # 7. Verify transition and events are persisted in database
    persisted_state = (
        db_session.query(SpacecraftStateRecord)
        .filter(SpacecraftStateRecord.run_id == run_id, SpacecraftStateRecord.mode == "SAFE_MODE")
        .first()
    )
    assert persisted_state is not None
    assert "OVERHEATING" in persisted_state.reason

    persisted_event = (
        db_session.query(EventRecord)
        .filter(EventRecord.run_id == run_id, EventRecord.event_type == "STATE_TRANSITION")
        .order_by(EventRecord.timestamp_sim.desc())
        .first()
    )
    assert persisted_event is not None
    assert "SAFE_MODE" in persisted_event.message

    incident = (
        db_session.query(IncidentRecord)
        .filter(IncidentRecord.run_id == run_id, IncidentRecord.fault_type == "OVERHEATING")
        .first()
    )
    assert incident is not None
    assert incident.status in ("OPEN", "ACKNOWLEDGED")

    # 8. Reduce temperature below 75°C (clear fault and cool down)
    simulator.clear_fault("OVERHEATING")
    simulator.temperature_c = 22.0

    # Step simulation again
    step_resp_2 = client.post("/api/v1/simulation/step?dt=1.0")
    assert step_resp_2.status_code == 200
    cool_data = step_resp_2.json()["telemetry"]
    assert cool_data["temperature_c"] < 75.0

    # 9. Verify state DOES NOT silently return to NOMINAL!
    assert simulator.current_mode == SpacecraftMode.SAFE_MODE
    assert cool_data["mode"] == "SAFE_MODE"

    # 10. Attempt invalid recovery while preconditions check or direct transition
    # Direct command to SET_MODE NOMINAL must be rejected
    invalid_cmd = client.post(
        "/api/v1/commands",
        json={"command_type": "SET_MODE", "parameters": {"target_mode": "NOMINAL"}},
    )
    assert invalid_cmd.status_code == 200
    assert invalid_cmd.json()["status"] == "REJECTED"

    # 11. Execute validated recovery request
    rec_resp = client.post(
        "/api/v1/state/recovery-request",
        json={"requested_by": "LEAD_OPERATOR", "reason": "Avionics bay cooled to 22C, telemetry stable."},
    )
    assert rec_resp.status_code == 200
    assert rec_resp.json()["final_mode"] == "NOMINAL"
    assert simulator.current_mode == SpacecraftMode.NOMINAL
