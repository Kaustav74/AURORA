"""
Complete Test Suite for Physics Lab Numerical Propagator, Propulsion,
Relativistic Geodesics, Anomaly Detection, and REST Endpoints.
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.physics_lab.models.newtonian import NewtonianModel
from app.physics_lab.models.ramanujan_pseries import RamanujanPSeriesOpeningModel
from app.physics_lab.models.schwarzschild import SchwarzschildRelativisticModel
from app.physics_lab.models.registry import PhysicsModelRegistry
from app.physics_lab.engine.propagator import OrbitPropagator
from app.physics_lab.engine.propulsion import PropulsionSubsystem
from app.physics_lab.analysis.anomaly_detector import AnomalyDetectorEngine
from app.physics_lab.analysis.parameter_fitter import ParameterFitterEngine


from app.db import init_db


@pytest.fixture
def client():
    init_db()
    return TestClient(app)


def test_propagator_newtonian_rk4_and_rk45_conservation():
    """Verify energy and angular momentum conservation in unpowered conservative orbit."""
    model = NewtonianModel()
    M = 1.989e30
    pos0 = np.array([1.496e11, 0.0, 0.0])
    vel0 = np.array([0.0, 29784.8, 0.0])

    # 1. Test Dormand-Prince adaptive integrator
    prop_dp = OrbitPropagator(model=model, central_mass=M, integrator_name="DORMAND_PRINCE", rtol=1e-8, atol=1e-10)
    out_dp = prop_dp.propagate(pos0, vel0, duration_seconds=86400.0 * 10, dt_initial=100.0)

    assert out_dp["termination_reason"] == "DURATION_REACHED"
    assert out_dp["max_energy_drift_rel"] < 1.0e-5
    assert len(out_dp["trajectory"]) > 0

    # 2. Test RK4 fixed-step integrator
    prop_rk4 = OrbitPropagator(model=model, central_mass=M, integrator_name="RK4")
    out_rk4 = prop_rk4.propagate(pos0, vel0, duration_seconds=86400.0 * 5, dt_initial=50.0)
    assert out_rk4["termination_reason"] == "DURATION_REACHED"
    assert out_rk4["max_energy_drift_rel"] < 1.0e-4


def test_propagator_schwarzschild_relativistic_precession():
    """Verify Model E relativistic geodesic integration and horizon bounds."""
    model = SchwarzschildRelativisticModel()
    M_bh = 10.0 * 1.989e30  # 10 Solar Mass Black Hole
    Rs = model.schwarzschild_radius(M_bh)
    r_isco = model.isco_radius(M_bh)
    r_photon = model.photon_sphere_radius(M_bh)

    assert np.isclose(Rs, 29532.5, rtol=1e-2)
    assert np.isclose(r_isco, 3.0 * Rs, rtol=1e-5)
    assert np.isclose(r_photon, 1.5 * Rs, rtol=1e-5)

    # Test stable circular orbit above ISCO: r = 5.0 * Rs
    # Period for 10 M_sun BH at 5 Rs is ~9.8 milliseconds
    r_orbit = 5.0 * Rs
    v_circ = model.circular_orbital_speed(r_orbit, M_bh)
    assert v_circ is not None

    prop = OrbitPropagator(model=model, central_mass=M_bh, integrator_name="DORMAND_PRINCE", dt_min=1e-7, dt_max=0.001)
    pos0 = np.array([r_orbit, 0.0, 0.0])
    vel0 = np.array([0.0, v_circ, 0.0])
    # Integrate for ~2 orbits (0.02 seconds) with sub-millisecond initial step
    out = prop.propagate(pos0, vel0, duration_seconds=0.02, dt_initial=0.0001)

    assert out["termination_reason"] == "DURATION_REACHED"
    # Spacecraft remained outside ISCO
    assert out["closest_approach_m"] > r_isco


def test_propulsion_and_mass_depletion():
    """Verify spacecraft propulsion, Tsiolkovsky mass depletion, and fuel exhaustion."""
    model = NewtonianModel()
    M = 1.989e30
    pos0 = np.array([1.496e11, 0.0, 0.0])
    vel0 = np.array([0.0, 29784.8, 0.0])

    # 100 kg fuel, 500 N thrust, 300s Isp -> mdot = 500 / (300 * 9.80665) = 0.17 kg/s
    propulsion = PropulsionSubsystem(
        dry_mass=500.0,
        propellant_mass=100.0,
        thrust_n=500.0,
        isp_seconds=300.0,
        maneuvers=[
            {"type": "CONTINUOUS", "t_start": 100.0, "t_end": 300.0, "direction_mode": "PROGRADE"}
        ]
    )

    prop = OrbitPropagator(model=model, central_mass=M, propulsion=propulsion, integrator_name="DORMAND_PRINCE")
    out = prop.propagate(pos0, vel0, duration_seconds=600.0, dt_initial=10.0)

    final_m = out["final_state"]["mass_kg"]
    final_prop = out["final_state"]["propellant_kg"]
    # Burn lasted 200s, burned ~34 kg of propellant
    assert final_prop < 100.0
    assert np.isclose(final_m, 500.0 + final_prop, atol=1e-3)


def test_anomaly_detection_horizon_crossing():
    """Verify AnomalyDetectorEngine detects black hole horizon crossing and critical findings."""
    model = SchwarzschildRelativisticModel()
    M_bh = 10.0 * 1.989e30
    Rs = model.schwarzschild_radius(M_bh)

    # Inward radial plunge starting just outside horizon
    pos0 = np.array([1.5 * Rs, 0.0, 0.0])
    vel0 = np.array([-1000.0, 0.0, 0.0])

    prop = OrbitPropagator(model=model, central_mass=M_bh, integrator_name="DORMAND_PRINCE")
    sim_out = prop.propagate(pos0, vel0, duration_seconds=100.0, dt_initial=0.01)

    assert sim_out["termination_reason"] == "HORIZON_CROSSING"

    # Analyze with Anomaly Engine
    detector = AnomalyDetectorEngine()
    findings = detector.analyze_simulation_run("EXP-TEST-01", sim_out)

    horizon_findings = [f for f in findings if f["category"] == "PHYSICAL_BOUNDARY"]
    assert len(horizon_findings) >= 1
    assert horizon_findings[0]["severity"] == "CRITICAL"
    assert "Schwarzschild Horizon" in horizon_findings[0]["title"]


def test_api_endpoints_physics_lab(client):
    """Verify REST API routes under /api/v1/physics-lab."""
    # 1. Models list
    res_models = client.get("/api/v1/physics-lab/models")
    assert res_models.status_code == 200
    models_list = res_models.json()
    assert len(models_list) >= 2
    model_ids = [m["model_id"] for m in models_list]
    assert "MODEL-A-NEWTONIAN" in model_ids
    assert "MODEL-B-RAMANUJAN-PSERIES-OPENING" in model_ids

    # 2. Validation summary
    res_val = client.get("/api/v1/physics-lab/validation/summary")
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["status"] == "OPERATIONAL"

    # 3. Create and execute experiment via API
    payload = {
        "name": "API Keplerian Test",
        "model_id": "MODEL-A-NEWTONIAN",
        "central_mass_kg": 1.989e30,
        "initial_position_m": [1.496e11, 0.0, 0.0],
        "initial_velocity_mps": [0.0, 29784.8, 0.0],
        "duration_seconds": 3600.0,
        "dt_initial": 60.0,
        "integrator": "DORMAND_PRINCE",
        "decimate_points": 50
    }
    res_exp = client.post("/api/v1/physics-lab/experiments", json=payload)
    assert res_exp.status_code == 200
    exp_data = res_exp.json()
    exp_id = exp_data["experiment_id"]
    assert exp_data["termination_reason"] == "DURATION_REACHED"

    # 4. Fetch trajectory
    res_traj = client.get(f"/api/v1/physics-lab/experiments/{exp_id}/trajectory")
    assert res_traj.status_code == 200
    traj_data = res_traj.json()
    assert traj_data["point_count"] > 0
    assert len(traj_data["points"]) > 0

    # 5. Fetch experiment detail
    res_detail = client.get(f"/api/v1/physics-lab/experiments/{exp_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == exp_id

    # 6. Export CSV
    res_csv = client.get(f"/api/v1/physics-lab/export/csv?experiment_id={exp_id}")
    assert res_csv.status_code == 200
    assert "t_sim_s,x_m,y_m,z_m" in res_csv.text

    # 7. Model comparison API
    comp_payload = {
        "name": "API Comparison",
        "model_ids": ["MODEL-A-NEWTONIAN", "MODEL-B-RAMANUJAN-PSERIES-OPENING"],
        "central_mass_kg": 1.989e30,
        "initial_position_m": [1.0e7, 0.0, 0.0],
        "initial_velocity_mps": [0.0, 3600.0, 0.0],
        "duration_seconds": 600.0,
        "integrator": "DORMAND_PRINCE"
    }
    res_comp = client.post("/api/v1/physics-lab/experiments/compare", json=comp_payload)
    assert res_comp.status_code == 200
    assert len(res_comp.json()["pairwise_comparisons"]) >= 1
