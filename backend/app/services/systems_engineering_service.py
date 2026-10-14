import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import (
    RequirementRecord,
    VerificationCaseRecord,
    RiskRecord,
    DesignDecisionRecord,
    InterfaceRecord,
    IssueRecord,
)
from app.schemas.systems_eng import (
    RequirementCreate,
    RequirementResponse,
    VerificationCaseCreate,
    VerificationCaseResponse,
    RiskCreate,
    RiskResponse,
    DecisionCreate,
    DecisionResponse,
    InterfaceCreate,
    InterfaceResponse,
    IssueCreate,
    IssueResponse,
    ReadinessSummaryResponse,
)

DEFAULT_REQUIREMENTS = [
    {
        "id": "REQ-TH-001",
        "title": "Thermal Safe Mode Transition",
        "statement": "When core avionics temperature reaches or exceeds 75.0°C, the system shall transition from NOMINAL to SAFE_MODE within 1 simulation tick.",
        "rationale": "Prevent catastrophic avionics component degradation during thermal runaway.",
        "priority": "HIGH",
        "category": "THERMAL",
        "verification_method": "TEST",
        "acceptance_criteria": "Temperature >= 75.0°C results in immediate state transition to SAFE_MODE and persistent event log entry.",
        "status": "ACTIVE",
    },
    {
        "id": "REQ-EPS-001",
        "title": "Bus Under-Voltage & Depletion Protection",
        "statement": "When battery SOC drops below 20.0% or bus voltage drops below 22.0V, the system shall transition to SAFE_MODE and shed non-essential loads.",
        "rationale": "Maintain battery chemistry stability and preserve essential housekeeping avionics.",
        "priority": "HIGH",
        "category": "POWER",
        "verification_method": "TEST",
        "acceptance_criteria": "SOC < 20% triggers SAFE_MODE and reduces current draw below 1.5A.",
        "status": "ACTIVE",
    },
    {
        "id": "REQ-CMD-001",
        "title": "Safe Mode Command Restriction",
        "statement": "While in SAFE_MODE, the command centre shall reject payload operations and arbitrary mode changes except validated recovery procedures and telemetry requests.",
        "rationale": "Prevent ground operators or automated scripts from executing harmful commands during spacecraft distress.",
        "priority": "HIGH",
        "category": "OPERATIONS",
        "verification_method": "TEST",
        "acceptance_criteria": "Commands unauthorized in SAFE_MODE return status REJECTED with explicit justification.",
        "status": "ACTIVE",
    },
    {
        "id": "REQ-REC-001",
        "title": "Deterministic Recovery Preconditions",
        "statement": "Recovery from SAFE_MODE shall require all preconditions (temp < 75°C, SOC >= 30%, link != LOST) to be verified before entering RECOVERY mode.",
        "rationale": "Prevent premature restoration of full loads before spacecraft systems have cooled and stabilized.",
        "priority": "HIGH",
        "category": "STATE_MACHINE",
        "verification_method": "TEST",
        "acceptance_criteria": "Recovery request rejected when temperature >= 75°C; accepted and promoted to NOMINAL only when all preconditions satisfied.",
        "status": "ACTIVE",
    },
    {
        "id": "REQ-DET-001",
        "title": "Deterministic Simulation Repeatability",
        "statement": "Given identical random seed and scenario inputs, repeated simulation runs shall produce identical telemetry and state sequences.",
        "rationale": "Enable reliable regression testing and verification of flight software procedures.",
        "priority": "MEDIUM",
        "category": "OPERATIONS",
        "verification_method": "TEST",
        "acceptance_criteria": "Run 1 and Run 2 telemetry match bit-for-bit when initialized with identical seed.",
        "status": "ACTIVE",
    },
    {
        "id": "REQ-LOG-001",
        "title": "Persistent State & Fault Event Auditing",
        "statement": "All state transitions, fault detections, and command attempts shall be recorded with simulation timestamp in persistent storage.",
        "rationale": "Ensure comprehensive post-pass telemetry analysis and incident forensics.",
        "priority": "MEDIUM",
        "category": "OPERATIONS",
        "verification_method": "TEST",
        "acceptance_criteria": "Database retains all records across application restarts.",
        "status": "ACTIVE",
    },
]

DEFAULT_VERIFICATION_CASES = [
    {
        "id": "VER-TH-001",
        "title": "Thermal Overheating Acceptance Test",
        "purpose": "Verify REQ-TH-001 by driving simulated temperature above 75.0°C and verifying state transition to SAFE_MODE.",
        "preconditions": "Spacecraft initialized in NOMINAL mode. Sim running.",
        "test_procedure": "1. Inject thermal fault target=78.5°C. 2. Advance step. 3. Query telemetry and spacecraft state.",
        "expected_result": "Telemetry temperature >= 75°C. State == SAFE_MODE. Event recorded in database.",
        "linked_requirement_ids": ["REQ-TH-001"],
    },
    {
        "id": "VER-EPS-001",
        "title": "Battery Depletion Protection Test",
        "purpose": "Verify REQ-EPS-001 by injecting low battery fault (<20% SOC).",
        "preconditions": "Spacecraft in NOMINAL mode.",
        "test_procedure": "1. Inject fault LOW_BATTERY target=16.0%. 2. Advance step. 3. Check current draw and state.",
        "expected_result": "State == SAFE_MODE. Current draw shed to ~1.2A.",
        "linked_requirement_ids": ["REQ-EPS-001"],
    },
    {
        "id": "VER-CMD-001",
        "title": "Restricted Command in SAFE_MODE Test",
        "purpose": "Verify REQ-CMD-001 by submitting ADJUST_PARAMETER while spacecraft is in SAFE_MODE.",
        "preconditions": "Spacecraft in SAFE_MODE.",
        "test_procedure": "1. Submit command ADJUST_PARAMETER. 2. Verify command status is REJECTED.",
        "expected_result": "Status is REJECTED with explicit reason.",
        "linked_requirement_ids": ["REQ-CMD-001"],
    },
    {
        "id": "VER-REC-001",
        "title": "Recovery Precondition Validation Test",
        "purpose": "Verify REQ-REC-001 by attempting recovery while temperature is high, then allowing cool down and verifying successful recovery.",
        "preconditions": "Spacecraft in SAFE_MODE with temperature > 75°C.",
        "test_procedure": "1. Attempt RECOVERY_REQUEST -> verify rejected. 2. Clear thermal fault and cool < 75°C. 3. Re-submit RECOVERY_REQUEST -> verify accepted.",
        "expected_result": "First request rejected. Second request transitions to RECOVERY then NOMINAL.",
        "linked_requirement_ids": ["REQ-REC-001"],
    },
    {
        "id": "VER-DET-001",
        "title": "Deterministic Repeatability Test",
        "purpose": "Verify REQ-DET-001 by executing SCN-NOMINAL twice with seed 42.",
        "preconditions": "Clean database or isolated run.",
        "test_procedure": "1. Run SCN-NOMINAL. 2. Run SCN-NOMINAL again. 3. Compare telemetry arrays.",
        "expected_result": "Identical telemetry values produced across both runs.",
        "linked_requirement_ids": ["REQ-DET-001"],
    },
    {
        "id": "VER-LOG-001",
        "title": "Restart Persistence Verification Test",
        "purpose": "Verify REQ-LOG-001 by creating events and reloading database session.",
        "preconditions": "Active SQLite database.",
        "test_procedure": "1. Record events and telemetry. 2. Close session. 3. Open fresh session and query records.",
        "expected_result": "All records retained intact.",
        "linked_requirement_ids": ["REQ-LOG-001"],
    },
]

DEFAULT_RISKS = [
    {
        "id": "RSK-001",
        "description": "Thermal radiator degradation causing avionics overheating during high solar incidence.",
        "likelihood": 3,
        "impact": 5,
        "score": 15,
        "mitigation": "Autonomous thermal watchdog threshold at 75°C with automatic payload shutdown and SAFE_MODE transition.",
        "owner": "Thermal Subsystem Lead",
        "status": "MITIGATED",
    },
    {
        "id": "RSK-002",
        "description": "Prolonged eclipse duration depleting secondary lithium-ion battery cells.",
        "likelihood": 2,
        "impact": 5,
        "score": 10,
        "mitigation": "Automated load shedding at 20% SOC with sleep cycles on non-critical instruments.",
        "owner": "Power Subsystem Lead",
        "status": "MITIGATED",
    },
    {
        "id": "RSK-003",
        "description": "Ground station tracking loss during key orbital pass.",
        "likelihood": 3,
        "impact": 3,
        "score": 9,
        "mitigation": "Autonomous attitude hold, onboard command queue buffer, and emergency beacon mode.",
        "owner": "Operations Lead",
        "status": "IDENTIFIED",
    },
]

DEFAULT_DECISIONS = [
    {
        "id": "ADR-001",
        "title": "Relational SQLite Persistence for Educational Testbench",
        "context": "Need zero-dependency, local-first persistence for repeatable spacecraft simulation runs and tests.",
        "decision": "Use SQLite with SQLAlchemy ORM. Avoid heavyweight external database servers like PostgreSQL for local execution.",
        "alternatives": "PostgreSQL, flat JSON files, MongoDB.",
        "consequences": "Fast, fully contained test suite; single file backup; straightforward migration path.",
        "status": "ACCEPTED",
    },
    {
        "id": "ADR-002",
        "title": "Two-Phase Command Lifecycle with Idempotency Validation",
        "context": "Spacecraft flight operations require strict command verification prior to subsystem execution.",
        "decision": "Commands progress through PENDING -> VALIDATED / REJECTED -> EXECUTING -> COMPLETED / FAILED with idempotency keys.",
        "alternatives": "Synchronous single-step REST endpoints without validation audit.",
        "consequences": "Prevents unauthorized commands from corrupting vehicle state and creates complete audit log.",
        "status": "ACCEPTED",
    },
    {
        "id": "ADR-003",
        "title": "Explicit State Machine & Precondition-Gated Safe Mode Recovery",
        "context": "Accidental or automatic return from SAFE_MODE to NOMINAL while root cause remains can destroy flight hardware.",
        "decision": "Direct SAFE_MODE to NOMINAL transition is prohibited. Operators must command RECOVERY, and backend verifies preconditions.",
        "alternatives": "Automatic hysteresis return to NOMINAL when temperature drops.",
        "consequences": "Ensures flight safety discipline and realistic operations workflow.",
        "status": "ACCEPTED",
    },
]

DEFAULT_INTERFACES = [
    {
        "id": "ICD-001",
        "name": "Ground Telemetry REST Interface",
        "producer": "AURORA Backend Telemetry Service",
        "consumer": "Operations Mission Control UI / Automation Scripts",
        "contract_spec": "JSON envelope with timestamp_sim, mode, temperatures, battery_soc, bus_voltage, comm_status.",
        "version": "1.0.0",
        "limitations": "Polled at 1Hz or queried via historical filters. Does not support real-time sub-millisecond bus captures.",
    },
    {
        "id": "ICD-002",
        "name": "Live Telemetry WebSocket Stream",
        "producer": "AURORA WebSocket Broadcaster",
        "consumer": "Mission Overview Dashboard",
        "contract_spec": "JSON frames: {'type': 'TELEMETRY_UPDATE', 'run_id': '...', 'timestamp': ..., 'data': {...}}",
        "version": "1.0.0",
        "limitations": "Local network only; client handles automatic reconnection and backoff.",
    },
]

DEFAULT_ISSUES = [
    {
        "id": "ISS-001",
        "title": "Thermal sensor noise margin tuning",
        "description": "Gaussian noise on simulated thermistors requires debounce filter to avoid flickering warning badges.",
        "severity": "MINOR",
        "status": "RESOLVED",
        "related_module": "fault_engine",
        "resolution_notes": "Implemented incident state deduplication in FaultEngine.",
    }
]

class SystemsEngineeringService:
    @staticmethod
    def seed_initial_records(db: Session) -> None:
        # Requirements
        for req in DEFAULT_REQUIREMENTS:
            if not db.query(RequirementRecord).filter(RequirementRecord.id == req["id"]).first():
                db.add(RequirementRecord(**req))
        # Verification Cases
        for vc in DEFAULT_VERIFICATION_CASES:
            if not db.query(VerificationCaseRecord).filter(VerificationCaseRecord.id == vc["id"]).first():
                rec = VerificationCaseRecord(
                    id=vc["id"],
                    title=vc["title"],
                    purpose=vc["purpose"],
                    preconditions=vc["preconditions"],
                    test_procedure=vc["test_procedure"],
                    expected_result=vc["expected_result"],
                    linked_requirement_ids_json=json.dumps(vc["linked_requirement_ids"]),
                    latest_status="NOT RUN",
                )
                db.add(rec)
        # Risks
        for rk in DEFAULT_RISKS:
            if not db.query(RiskRecord).filter(RiskRecord.id == rk["id"]).first():
                db.add(RiskRecord(**rk))
        # ADRs
        for adr in DEFAULT_DECISIONS:
            if not db.query(DesignDecisionRecord).filter(DesignDecisionRecord.id == adr["id"]).first():
                db.add(DesignDecisionRecord(**adr))
        # Interfaces
        for icd in DEFAULT_INTERFACES:
            if not db.query(InterfaceRecord).filter(InterfaceRecord.id == icd["id"]).first():
                db.add(InterfaceRecord(**icd))
        # Issues
        for iss in DEFAULT_ISSUES:
            if not db.query(IssueRecord).filter(IssueRecord.id == iss["id"]).first():
                db.add(IssueRecord(**iss))
        db.commit()

    @staticmethod
    def get_requirements(db: Session) -> List[RequirementResponse]:
        SystemsEngineeringService.seed_initial_records(db)
        reqs = db.query(RequirementRecord).all()
        cases = db.query(VerificationCaseRecord).all()

        # Build mapping of requirement_id -> linked tests & latest test statuses
        req_to_tests = {}
        for c in cases:
            linked = json.loads(c.linked_requirement_ids_json) if c.linked_requirement_ids_json else []
            for rid in linked:
                if rid not in req_to_tests:
                    req_to_tests[rid] = []
                req_to_tests[rid].append(c)

        result = []
        for r in reqs:
            linked_cases = req_to_tests.get(r.id, [])
            linked_ids = [c.id for c in linked_cases]
            if not linked_cases:
                ver_status = "UNLINKED"
            elif any(c.latest_status == "FAIL" for c in linked_cases):
                ver_status = "FAIL"
            elif all(c.latest_status == "PASS" for c in linked_cases):
                ver_status = "PASS"
            elif any(c.latest_status == "BLOCKED" for c in linked_cases):
                ver_status = "BLOCKED"
            else:
                ver_status = "NOT RUN"

            result.append(RequirementResponse(
                id=r.id,
                title=r.title,
                statement=r.statement,
                rationale=r.rationale,
                priority=r.priority,
                category=r.category,
                verification_method=r.verification_method,
                acceptance_criteria=r.acceptance_criteria,
                status=r.status,
                linked_test_ids=linked_ids,
                verification_status=ver_status,
            ))
        return result

    @staticmethod
    def get_verification_cases(db: Session) -> List[VerificationCaseResponse]:
        SystemsEngineeringService.seed_initial_records(db)
        cases = db.query(VerificationCaseRecord).all()
        return [
            VerificationCaseResponse(
                id=c.id,
                title=c.title,
                purpose=c.purpose,
                preconditions=c.preconditions,
                test_procedure=c.test_procedure,
                expected_result=c.expected_result,
                linked_requirement_ids=json.loads(c.linked_requirement_ids_json) if c.linked_requirement_ids_json else [],
                latest_status=c.latest_status,
                executed_at=c.executed_at,
                evidence_summary=c.evidence_summary,
            )
            for c in cases
        ]

    @staticmethod
    def record_verification_result(
        db: Session, case_id: str, status: str, evidence: str
    ) -> VerificationCaseRecord:
        case = db.query(VerificationCaseRecord).filter(VerificationCaseRecord.id == case_id).first()
        if not case:
            raise ValueError(f"Verification case '{case_id}' not found.")
        case.latest_status = status
        case.executed_at = datetime.utcnow()
        case.evidence_summary = evidence
        db.commit()
        db.refresh(case)
        return case

    @staticmethod
    def get_readiness_summary(db: Session) -> ReadinessSummaryResponse:
        reqs = SystemsEngineeringService.get_requirements(db)
        cases = db.query(VerificationCaseRecord).all()
        risks = db.query(RiskRecord).all()
        issues = db.query(IssueRecord).all()

        total_reqs = len(reqs)
        verified_reqs = sum(1 for r in reqs if r.verification_status == "PASS")
        unverified_reqs = total_reqs - verified_reqs
        unlinked_reqs = sum(1 for r in reqs if r.verification_status == "UNLINKED")
        coverage_pct = round((verified_reqs / total_reqs * 100.0) if total_reqs > 0 else 0.0, 1)

        total_cases = len(cases)
        passed_cases = sum(1 for c in cases if c.latest_status == "PASS")
        failed_cases = sum(1 for c in cases if c.latest_status == "FAIL")
        not_run_cases = sum(1 for c in cases if c.latest_status == "NOT RUN")
        blocked_cases = sum(1 for c in cases if c.latest_status == "BLOCKED")

        open_risks = sum(1 for rk in risks if rk.status in ("IDENTIFIED", "MITIGATED"))
        critical_risks = sum(1 for rk in risks if rk.score >= 15 and rk.status != "CLOSED")
        open_issues = sum(1 for i in issues if i.status in ("OPEN", "IN_PROGRESS"))

        if failed_cases > 0:
            assessment = "BLOCKED_BY_FAILURES: One or more critical verification cases failed."
        elif coverage_pct >= 80.0:
            assessment = "READY_FOR_SIMULATION_REVIEW: Core requirements verified with evidence."
        else:
            assessment = "IN_PROGRESS: Verification cases pending test suite execution."

        return ReadinessSummaryResponse(
            total_requirements=total_reqs,
            verified_requirements=verified_reqs,
            unverified_requirements=unverified_reqs,
            unlinked_requirements=unlinked_reqs,
            requirement_coverage_pct=coverage_pct,
            total_verification_cases=total_cases,
            cases_passed=passed_cases,
            cases_failed=failed_cases,
            cases_not_run=not_run_cases,
            cases_blocked=blocked_cases,
            open_risks_count=open_risks,
            critical_risks_count=critical_risks,
            open_issues_count=open_issues,
            readiness_assessment=assessment,
        )
