def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "version" in data
    assert "SIMULATION" in data["disclaimer"]

def test_metadata_endpoint(client):
    response = client.get("/api/v1/metadata")
    assert response.status_code == 200
    data = response.json()
    assert data["overheat_threshold_c"] == 75.0
    assert data["allow_dev_fault_injection"] is False
