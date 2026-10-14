"""
Phase 1 Mathematical Foundation Tests
Tests Model A (Newtonian baseline) and Model B (Ramanujan p-series opening model)
including derivative verification, normalization, parameter validation, and circular orbit checks.
"""

import pytest
import numpy as np
from app.physics_lab.models.newtonian import NewtonianModel
from app.physics_lab.models.ramanujan_pseries import RamanujanPSeriesOpeningModel
from app.physics_lab.models.registry import PhysicsModelRegistry


def test_model_a_newtonian_analytical_benchmarks():
    """Verify Model A against classical analytical Keplerian solutions."""
    model = NewtonianModel()
    M_sun = 1.989e30
    R_earth = 1.496e11  # 1 AU

    # Circular velocity v = sqrt(GM/r)
    v_circ = model.circular_orbital_speed(R_earth, M_sun)
    assert v_circ is not None
    # 29,784.8 m/s expected for Earth circular orbit around Sun
    assert np.isclose(v_circ, 29784.8, rtol=1e-3)

    # Orbital period T = 2*pi*r / v_circ
    period = model.orbital_period(R_earth, M_sun)
    assert period is not None
    seconds_in_year = 365.256 * 86400
    assert np.isclose(period, seconds_in_year, rtol=1e-3)

    # Energy in circular orbit: E = 0.5*v^2 - GM/r = -0.5 * GM/r
    pos = np.array([R_earth, 0.0, 0.0])
    vel = np.array([0.0, v_circ, 0.0])
    energy = model.specific_orbital_energy(pos, vel, M_sun)
    expected_energy = -0.5 * (6.67430e-11 * M_sun) / R_earth
    assert np.isclose(energy, expected_energy, rtol=1e-5)

    # Specific angular momentum: h = r x v = [0, 0, r * v]
    h_vec = model.specific_angular_momentum(pos, vel)
    assert np.isclose(h_vec[2], R_earth * v_circ, rtol=1e-7)

    # Singularity check
    with pytest.raises(ValueError, match="Coordinate singularity"):
        model.evaluate_potential(0.0, M_sun)


def test_model_b_ramanujan_pseries_normalization_and_derivatives():
    """
    Verify Model B:
    1. Normalization at R_ref strictly equals 1.0
    2. Analytical derivative dK_hat/dR matches central finite difference
    3. Potential at R_ref equals standard Newtonian potential
    """
    R0 = 1.0e6
    R_ref = 1.0e7
    model = RamanujanPSeriesOpeningModel(parameters={"R0": R0, "R_ref": R_ref, "N_terms": 500})
    M = 1.989e30

    # 1. Normalization check: K_hat(R_ref) == 1.0
    K_ref_val = model.evaluate_normalized_K(R_ref)
    assert np.isclose(K_ref_val, 1.0, atol=1e-12)

    # 2. At R_ref, potential must match classical Newtonian potential
    phi_model_b = model.evaluate_potential(R_ref, M)
    phi_newton = -(6.67430e-11 * M) / R_ref
    assert np.isclose(phi_model_b, phi_newton, rtol=1e-9)

    # 3. Verify analytical derivative vs independent central finite difference across test radii
    test_radii = [0.2 * R0, 0.5 * R0, 1.0 * R0, 2.0 * R0, 5.0 * R0, R_ref, 2.0 * R_ref]
    for r in test_radii:
        dK_analytic = model.evaluate_normalized_dK_dR(r)
        dK_fd = model.evaluate_dK_dR_finite_difference(r, rel_step=1e-5)
        # Agreement within 1e-4 relative tolerance validates the analytical chain rule derivation
        assert np.isclose(dK_analytic, dK_fd, rtol=1e-4, atol=1e-15), (
            f"Derivative mismatch at r={r}: analytic={dK_analytic}, fd={dK_fd}"
        )


def test_model_b_parameter_validation_and_invalid_orbits():
    """Verify physical bounds, parameter constraints, and non-absolute value circular speed."""
    # Reject non-positive R0
    with pytest.raises(ValueError, match="R0 must be strictly positive"):
        RamanujanPSeriesOpeningModel(parameters={"R0": -5.0})

    # Reject s <= 1.0
    with pytest.raises(ValueError, match="Re\\(s\\) must be > 1"):
        RamanujanPSeriesOpeningModel(parameters={"s": 1.0})

    # Reject negative integer r
    with pytest.raises(ValueError, match="r must not be a negative integer"):
        RamanujanPSeriesOpeningModel(parameters={"r": -2.0})

    # Non-negative radicand constraint for circular speed
    model = RamanujanPSeriesOpeningModel(parameters={"R0": 1.0e6, "R_ref": 1.0e7})
    # For valid physical radius, returns real float
    v_c = model.circular_orbital_speed(1.0e7, 1.989e30)
    assert v_c is not None and v_c > 0.0


def test_model_b_horizon_approach_indicator():
    """Verify mathematical horizon diagnostic H(R): H -> 1 as R -> 0, H -> 0 as R -> R_far."""
    model = RamanujanPSeriesOpeningModel(parameters={"R0": 1.0e6, "R_far": 1.0e9})
    # Near center
    h_near = model.horizon_approach_indicator(1.0e4)  # R << R0
    assert h_near > 0.9  # Rises toward 1.0

    # Far from center
    h_far = model.horizon_approach_indicator(1.0e9)  # R == R_far
    assert np.isclose(h_far, 0.0, atol=1e-3)


def test_model_registry_metadata_and_factory():
    """Verify Model Registry loads metadata and creates verified instances."""
    models = PhysicsModelRegistry.list_models()
    assert len(models) >= 2

    # Instantiate Model A
    inst_a = PhysicsModelRegistry.create_model_instance("MODEL-A-NEWTONIAN")
    assert inst_a.model_id == "MODEL-A-NEWTONIAN"

    # Instantiate Model B
    inst_b = PhysicsModelRegistry.create_model_instance("MODEL-B-RAMANUJAN-PSERIES-OPENING")
    assert inst_b.model_id == "MODEL-B-RAMANUJAN-PSERIES-OPENING"

    # Reject unimplemented
    with pytest.raises(KeyError, match="not yet implemented"):
        PhysicsModelRegistry.create_model_instance("MODEL-NON-EXISTENT")
