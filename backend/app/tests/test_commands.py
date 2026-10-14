import pytest
from app.schemas.state import SpacecraftMode
from app.db.models import CommandRecord
from app.services.simulation_engine import simulator

def test_command_execution_and_idempotency(client, db_session):
    # Ensure nominal mode
    simulator.current_mode = SpacecraftMode.NOMINAL

    # 1. Valid PING command
    res1 = client.post(
        "/api/v1/commands",
        json={
            "command_type": "PING",
            "parameters": {},
            "idempotency_key": "IDEM-PING-001",
            "issued_by": "SYS_ADMIN",
        },
    )
    assert res1.status_code == 200
    cmd1 = res1.json()
    assert cmd1["status"] == "COMPLETED"
    assert cmd1["result"]["pong"] is True

    # 2. Duplicate submission with same idempotency key returns cached record
    res2 = client.post(
        "/api/v1/commands",
        json={
            "command_type": "PING",
            "parameters": {},
            "idempotency_key": "IDEM-PING-001",
        },
    )
    assert res2.status_code == 200
    assert res2.json()["id"] == cmd1["id"]

    # 3. Invalid parameter adjustment rejected
    res3 = client.post(
        "/api/v1/commands",
        json={
            "command_type": "ADJUST_PARAMETER",
            "parameters": {"parameter_name": "forbidden_thruster_valve", "value": 100},
        },
    )
    assert res3.status_code == 200
    cmd3 = res3.json()
    assert cmd3["status"] == "REJECTED"
    assert "not recognized" in cmd3["rejection_reason"]

    # 4. Safe mode restriction
    simulator.current_mode = SpacecraftMode.SAFE_MODE
    res4 = client.post(
        "/api/v1/commands",
        json={
            "command_type": "ADJUST_PARAMETER",
            "parameters": {"parameter_name": "cadence_hz", "value": 2.0},
        },
    )
    assert res4.status_code == 200
    cmd4 = res4.json()
    assert cmd4["status"] == "REJECTED"
    assert "restricted while spacecraft is in SAFE_MODE" in cmd4["rejection_reason"]

    # Restore nominal
    simulator.current_mode = SpacecraftMode.NOMINAL
