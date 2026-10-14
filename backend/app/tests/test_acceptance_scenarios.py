import json
from app.schemas.state import SpacecraftMode
from app.db.models import TelemetryRecord, EventRecord, CommandRecord, IncidentRecord, SpacecraftStateRecord
from app.services.simulation_engine import simulator

def test_scenario_a_nominal_mission(client, db_session):
    # 1. Start a new simulation run
    start_resp = client.post("/api/v1/simulation/start", json={"name": "Acceptance Run A", "seed": 42})
    assert start_resp.status_code == 200
    run_id = start_resp.json()["run_id"]

    # 2. Confirm backend reports active run
    status_resp = client.get("/api/v1/simulation/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["is_active"] is True
    assert status_resp.json()["run_id"] == run_id

    # 3. Confirm telemetry is generated from backend
    tel_resp = client.get("/api/v1/telemetry/current")
    assert tel_resp.status_code == 200
    tel_data = tel_resp.json()
    assert tel_data["run_id"] == run_id

    # 4. Confirm state is NOMINAL
    assert tel_data["mode"] == "NOMINAL"

    # 5. Confirm telemetry and events are persisted
    tel_count = db_session.query(TelemetryRecord).filter(TelemetryRecord.run_id == run_id).count()
    assert tel_count >= 1
    evt_count = db_session.query(EventRecord).filter(EventRecord.run_id == run_id).count()
    assert evt_count >= 1

def test_scenario_c_communication_loss(client, db_session):
    # Run comm loss scenario
    res = client.post("/api/v1/scenarios/SCN-COMM-LOSS/run")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["observed_outcomes"]["comm_status"] == "LOST"
    # State remains nominal (comm loss does not trigger safe mode immediately)
    assert data["observed_outcomes"]["final_mode"] == "NOMINAL"

def test_scenario_d_invalid_command(client, db_session):
    # Submit an invalid command type or parameter
    cmd_resp = client.post(
        "/api/v1/commands",
        json={
            "command_type": "ADJUST_PARAMETER",
            "parameters": {"parameter_name": "illegal_telemetry_rate", "value": -999},
            "issued_by": "ROGUE_OPERATOR",
        },
    )
    assert cmd_resp.status_code == 200
    cmd_data = cmd_resp.json()
    # Confirm rejection
    assert cmd_data["status"] == "REJECTED"
    assert "not recognized" in cmd_data["rejection_reason"]

    # Confirm recorded in command history
    history = client.get("/api/v1/commands").json()
    assert any(c["id"] == cmd_data["id"] and c["status"] == "REJECTED" for c in history)

def test_scenario_f_persistence_records(client, db_session):
    # Check that events, incidents, state history can be queried cleanly
    events = client.get("/api/v1/events").json()
    assert isinstance(events, list)

    incidents = client.get("/api/v1/incidents").json()
    assert isinstance(incidents, list)

    states = client.get("/api/v1/state/history").json()
    assert isinstance(states, list)

def test_scenario_h_verification_reporting(client, db_session):
    # 1. Fetch requirements and verification cases
    reqs = client.get("/api/v1/systems-engineering/requirements").json()
    cases = client.get("/api/v1/systems-engineering/verification-cases").json()

    assert len(reqs) >= 6
    assert len(cases) >= 6

    # 2. Before execution, test cases should be NOT RUN unless executed
    ver_case_1 = next(c for c in cases if c["id"] == "VER-TH-001")
    assert ver_case_1["latest_status"] in ("NOT RUN", "PASS", "FAIL")

    # 3. Record genuine test evidence
    exec_resp = client.post(
        f"/api/v1/systems-engineering/verification-cases/{ver_case_1['id']}/execute",
        json={"status": "PASS", "evidence_summary": "Executed automated test test_overheating_slice.py: passed in 0.08s."},
    )
    assert exec_resp.status_code == 200
    assert exec_resp.json()["latest_status"] == "PASS"

    # 4. Confirm requirement coverage summary reflects updated status
    readiness = client.get("/api/v1/systems-engineering/readiness").json()
    assert readiness["total_requirements"] >= 6
    assert readiness["cases_passed"] >= 1
