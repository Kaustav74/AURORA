def test_scenario_lab_runs(client):
    # 1. Get preloaded scenarios
    resp = client.get("/api/v1/scenarios")
    assert resp.status_code == 200
    scenarios = resp.json()
    assert len(scenarios) >= 5
    ids = [s["id"] for s in scenarios]
    assert "SCN-NOMINAL" in ids
    assert "SCN-OVERHEAT-GRADUAL" in ids

    # 2. Run Nominal scenario
    nom_run = client.post("/api/v1/scenarios/SCN-NOMINAL/run")
    assert nom_run.status_code == 200
    nom_data = nom_run.json()
    assert nom_data["status"] == "COMPLETED"
    assert nom_data["pass_fail"] == "PASS"
    assert nom_data["observed_outcomes"]["final_mode"] == "NOMINAL"

    # 3. Run Gradual Overheating scenario
    overheat_run = client.post("/api/v1/scenarios/SCN-OVERHEAT-GRADUAL/run")
    assert overheat_run.status_code == 200
    oh_data = overheat_run.json()
    assert oh_data["status"] == "COMPLETED"
    assert oh_data["pass_fail"] == "PASS"
    assert oh_data["observed_outcomes"]["final_mode"] == "SAFE_MODE"
    assert oh_data["observed_outcomes"]["safe_mode_triggered"] is True
