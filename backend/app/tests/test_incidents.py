from app.services.incident_service import IncidentService
from app.schemas.incident import IncidentSeverity
from app.db.models import IncidentRecord

def test_incident_lifecycle(client, db_session):
    # Create test incident
    inc = IncidentRecord(
        id="INC-TEST-001",
        run_id="TEST-RUN",
        fault_type="TEST_FAULT",
        severity="WARNING",
        status="OPEN",
        summary="Test Fault Detected",
        details="Telemetry sensor spike observed",
        first_seen_sim=10.0,
        last_seen_sim=10.0,
    )
    db_session.add(inc)
    db_session.commit()

    # Query incidents
    resp = client.get("/api/v1/incidents")
    assert resp.status_code == 200
    incidents = resp.json()
    assert any(i["id"] == "INC-TEST-001" for i in incidents)

    # Acknowledge incident
    ack_resp = client.post(
        "/api/v1/incidents/INC-TEST-001/acknowledge",
        json={"acknowledged_by": "OPERATOR_ALICE"},
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "ACKNOWLEDGED"
    assert ack_resp.json()["acknowledged_by"] == "OPERATOR_ALICE"

    # Resolve incident
    res_resp = client.post(
        "/api/v1/incidents/INC-TEST-001/resolve",
        json={"reason": "Sensor calibrated and transient cleared.", "resolved_by": "OPERATOR_ALICE"},
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"
    assert res_resp.json()["resolution_reason"] == "Sensor calibrated and transient cleared."
