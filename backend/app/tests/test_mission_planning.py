from app.db.models import MissionTask
from app.services.mission_planning_service import MissionPlanningService
from app.schemas.mission_plan import MissionTaskCreate

def test_mission_planning_schedule_and_cycles(client, db_session):
    # Clean tasks table
    db_session.query(MissionTask).delete()
    db_session.commit()

    # Create Task 1 (Detumble)
    t1 = client.post(
        "/api/v1/tasks",
        json={
            "id": "TSK-01",
            "title": "Spacecraft Detumble",
            "description": "Rate damping using ADCS magnetorquers",
            "priority": 1,
            "duration_minutes": 30,
            "earliest_start_minutes": 0,
            "deadline_minutes": 60,
            "dependencies": [],
        },
    )
    assert t1.status_code == 200

    # Create Task 2 (Solar Array Deploy, depends on TSK-01)
    t2 = client.post(
        "/api/v1/tasks",
        json={
            "id": "TSK-02",
            "title": "Solar Array Deployment",
            "description": "Release solar array retention pins",
            "priority": 1,
            "duration_minutes": 15,
            "earliest_start_minutes": 0,
            "deadline_minutes": 90,
            "dependencies": ["TSK-01"],
        },
    )
    assert t2.status_code == 200

    # Generate schedule
    sched_resp = client.post("/api/v1/schedules/generate")
    assert sched_resp.status_code == 200
    sched_data = sched_resp.json()
    assert sched_data["success"] is True
    assert sched_data["scheduled_tasks"] == 2
    tasks = {t["id"]: t for t in sched_data["tasks"]}
    assert tasks["TSK-01"]["scheduled_start_minutes"] == 0
    assert tasks["TSK-01"]["scheduled_end_minutes"] == 30
    assert tasks["TSK-02"]["scheduled_start_minutes"] == 30
    assert tasks["TSK-02"]["scheduled_end_minutes"] == 45

    # Introduce a circular dependency (TSK-01 depends on TSK-02)
    client.put(
        "/api/v1/tasks/TSK-01",
        json={"dependencies": ["TSK-02"]},
    )

    cycle_sched = client.post("/api/v1/schedules/generate")
    assert cycle_sched.status_code == 200
    cycle_data = cycle_sched.json()
    assert cycle_data["success"] is False
    assert any("Dependency cycle detected" in c for c in cycle_data["conflicts"])
