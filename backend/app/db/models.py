from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from app.db.session import Base

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="STOPPED")  # STOPPED, RUNNING, PAUSED
    seed = Column(Integer, nullable=False, default=42)
    cadence_hz = Column(Float, nullable=False, default=1.0)
    sim_time_seconds = Column(Float, nullable=False, default=0.0)
    start_wall_time = Column(DateTime, default=datetime.utcnow)
    updated_wall_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config_json = Column(Text, nullable=True)

class SpacecraftStateRecord(Base):
    __tablename__ = "spacecraft_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(36), ForeignKey("simulation_runs.id"), nullable=False, index=True)
    mode = Column(String(30), nullable=False)  # STANDBY, NOMINAL, DEGRADED, SAFE_MODE, RECOVERY, SIMULATION_STOPPED
    previous_mode = Column(String(30), nullable=True)
    reason = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)
    timestamp_sim = Column(Float, nullable=False, index=True)
    timestamp_wall = Column(DateTime, default=datetime.utcnow)

class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(36), ForeignKey("simulation_runs.id"), nullable=False, index=True)
    timestamp_sim = Column(Float, nullable=False, index=True)
    timestamp_wall = Column(DateTime, default=datetime.utcnow)
    mode = Column(String(30), nullable=False)
    temperature_c = Column(Float, nullable=False)
    battery_soc_pct = Column(Float, nullable=False)
    bus_voltage_v = Column(Float, nullable=False)
    current_draw_a = Column(Float, nullable=False)
    comm_status = Column(String(20), nullable=False)  # NOMINAL, DEGRADED, LOST
    signal_quality_pct = Column(Float, nullable=False)
    attitude_error_deg = Column(Float, nullable=False)
    angular_rate_deg_s = Column(Float, nullable=False)
    storage_used_pct = Column(Float, nullable=False)
    sensors_valid = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=True)

class CommandRecord(Base):
    __tablename__ = "commands"

    id = Column(String(36), primary_key=True)
    run_id = Column(String(36), nullable=True, index=True)
    idempotency_key = Column(String(100), nullable=True, index=True)
    command_type = Column(String(50), nullable=False)
    parameters_json = Column(Text, nullable=False)
    issued_by = Column(String(50), nullable=False, default="OPERATOR")
    status = Column(String(20), nullable=False)  # PENDING, VALIDATED, REJECTED, EXECUTING, COMPLETED, FAILED
    rejection_reason = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

class IncidentRecord(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True)
    run_id = Column(String(36), nullable=True, index=True)
    fault_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # WARNING, CRITICAL
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN, ACKNOWLEDGED, RESOLVED, FALSE_POSITIVE
    summary = Column(String(255), nullable=False)
    details = Column(Text, nullable=False)
    first_seen_sim = Column(Float, nullable=False)
    last_seen_sim = Column(Float, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(50), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_reason = Column(Text, nullable=True)
    telemetry_snapshot_json = Column(Text, nullable=True)

class EventRecord(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True)
    run_id = Column(String(36), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="INFO")  # INFO, WARNING, CRITICAL
    message = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    timestamp_sim = Column(Float, nullable=False, index=True)
    timestamp_wall = Column(DateTime, default=datetime.utcnow)

class MissionTask(Base):
    __tablename__ = "mission_tasks"

    id = Column(String(50), primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, default=2)  # 1=Critical, 2=High, 3=Medium, 4=Low
    duration_minutes = Column(Integer, nullable=False)
    earliest_start_minutes = Column(Integer, nullable=False, default=0)
    deadline_minutes = Column(Integer, nullable=True)
    dependencies_json = Column(Text, nullable=False, default="[]")
    resources_json = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="UNSCHEDULED")
    scheduled_start_minutes = Column(Integer, nullable=True)
    scheduled_end_minutes = Column(Integer, nullable=True)
    scheduling_notes = Column(Text, nullable=True)

class ScenarioDefinition(Base):
    __tablename__ = "scenario_definitions"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    seed = Column(Integer, nullable=False, default=42)
    initial_config_json = Column(Text, nullable=False, default="{}")
    fault_schedule_json = Column(Text, nullable=False, default="[]")
    expected_outcomes_json = Column(Text, nullable=False, default="{}")
    version = Column(String(20), nullable=False, default="1.0.0")

class ScenarioRunRecord(Base):
    __tablename__ = "scenario_runs"

    id = Column(String(36), primary_key=True)
    scenario_id = Column(String(50), ForeignKey("scenario_definitions.id"), nullable=False)
    run_id = Column(String(36), nullable=True)
    status = Column(String(20), nullable=False, default="RUNNING")
    seed = Column(Integer, nullable=False)
    observed_outcomes_json = Column(Text, nullable=True)
    pass_fail = Column(String(10), nullable=True)  # PASS, FAIL
    deviations_json = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class RequirementRecord(Base):
    __tablename__ = "requirements"

    id = Column(String(50), primary_key=True)  # e.g., REQ-TH-001
    title = Column(String(150), nullable=False)
    statement = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="HIGH")
    category = Column(String(50), nullable=False)  # THERMAL, POWER, COMMS, ADCS, STATE_MACHINE, OPERATIONS
    verification_method = Column(String(50), nullable=False)  # TEST, ANALYSIS, INSPECTION, DEMONSTRATION
    acceptance_criteria = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")

class VerificationCaseRecord(Base):
    __tablename__ = "verification_cases"

    id = Column(String(50), primary_key=True)  # e.g., VER-TH-001
    title = Column(String(150), nullable=False)
    purpose = Column(Text, nullable=False)
    preconditions = Column(Text, nullable=False)
    test_procedure = Column(Text, nullable=False)
    expected_result = Column(Text, nullable=False)
    linked_requirement_ids_json = Column(Text, nullable=False, default="[]")
    latest_status = Column(String(20), nullable=False, default="NOT RUN")  # NOT RUN, PASS, FAIL, BLOCKED
    executed_at = Column(DateTime, nullable=True)
    evidence_summary = Column(Text, nullable=True)

class RiskRecord(Base):
    __tablename__ = "risks"

    id = Column(String(50), primary_key=True)
    description = Column(Text, nullable=False)
    likelihood = Column(Integer, nullable=False)  # 1-5
    impact = Column(Integer, nullable=False)      # 1-5
    score = Column(Integer, nullable=False)
    mitigation = Column(Text, nullable=False)
    owner = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="IDENTIFIED")
    review_date = Column(DateTime, nullable=True)

class DesignDecisionRecord(Base):
    __tablename__ = "design_decisions"

    id = Column(String(50), primary_key=True)  # ADR-001
    title = Column(String(150), nullable=False)
    context = Column(Text, nullable=False)
    decision = Column(Text, nullable=False)
    alternatives = Column(Text, nullable=False)
    consequences = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="ACCEPTED")
    date = Column(DateTime, default=datetime.utcnow)

class InterfaceRecord(Base):
    __tablename__ = "interfaces"

    id = Column(String(50), primary_key=True)  # ICD-001
    name = Column(String(150), nullable=False)
    producer = Column(String(100), nullable=False)
    consumer = Column(String(100), nullable=False)
    contract_spec = Column(Text, nullable=False)
    version = Column(String(20), nullable=False, default="1.0.0")
    limitations = Column(Text, nullable=False)

class IssueRecord(Base):
    __tablename__ = "issues"

    id = Column(String(50), primary_key=True)  # ISS-001
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="MAJOR")  # CRITICAL, MAJOR, MINOR
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    related_module = Column(String(50), nullable=False)
    resolution_notes = Column(Text, nullable=True)


class PhysicsExperimentRecord(Base):
    __tablename__ = "physics_experiments"

    id = Column(String(36), primary_key=True)
    name = Column(String(150), nullable=False)
    model_id = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=False, default="1.0.0")
    central_mass_kg = Column(Float, nullable=False)
    status = Column(String(30), nullable=False, default="COMPLETED")  # PENDING, RUNNING, COMPLETED, FAILED
    termination_reason = Column(String(50), nullable=False, default="DURATION_REACHED")
    integrator = Column(String(50), nullable=False, default="DORMAND_PRINCE")
    sim_duration_s = Column(Float, nullable=False, default=0.0)
    closest_approach_m = Column(Float, nullable=True)
    farthest_distance_m = Column(Float, nullable=True)
    max_energy_drift = Column(Float, nullable=True)
    config_json = Column(Text, nullable=True)
    summary_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PhysicsTrajectoryRecord(Base):
    __tablename__ = "physics_trajectories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(36), ForeignKey("physics_experiments.id"), nullable=False, index=True)
    point_count = Column(Integer, nullable=False, default=0)
    trajectory_json = Column(Text, nullable=False)


class PhysicsAnomalyRecord(Base):
    __tablename__ = "physics_anomalies"

    id = Column(String(50), primary_key=True)
    experiment_id = Column(String(36), ForeignKey("physics_experiments.id"), nullable=False, index=True)
    time_sim = Column(Float, nullable=False)
    model_id = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # NUMERICAL_FAILURE, PHYSICAL_BOUNDARY, NUMERICAL_CONVERGENCE, etc.
    severity = Column(String(20), nullable=False)  # CRITICAL, WARNING, INFO
    title = Column(String(200), nullable=False)
    explanation = Column(Text, nullable=False)
    detection_rule = Column(String(100), nullable=False)
    observed_value = Column(String(100), nullable=True)
    reference_value = Column(String(100), nullable=True)
    residual = Column(Float, nullable=True)
    threshold = Column(String(100), nullable=True)
    status = Column(String(30), nullable=False, default="NEW")  # NEW, INVESTIGATING, REPRODUCED, RESOLVED, DISMISSED
    recommended_action = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
