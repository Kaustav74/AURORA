from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class RequirementCreate(BaseModel):
    id: str
    title: str
    statement: str
    rationale: str
    priority: str = "HIGH"
    category: str
    verification_method: str = "TEST"
    acceptance_criteria: str
    status: str = "ACTIVE"

class RequirementResponse(BaseModel):
    id: str
    title: str
    statement: str
    rationale: str
    priority: str
    category: str
    verification_method: str
    acceptance_criteria: str
    status: str
    linked_test_ids: List[str] = Field(default_factory=list)
    verification_status: str = "NOT RUN"  # NOT RUN, PASS, FAIL, BLOCKED, UNLINKED

class VerificationCaseCreate(BaseModel):
    id: str
    title: str
    purpose: str
    preconditions: str
    test_procedure: str
    expected_result: str
    linked_requirement_ids: List[str] = Field(default_factory=list)

class VerificationCaseResponse(BaseModel):
    id: str
    title: str
    purpose: str
    preconditions: str
    test_procedure: str
    expected_result: str
    linked_requirement_ids: List[str]
    latest_status: str
    executed_at: Optional[datetime] = None
    evidence_summary: Optional[str] = None

class VerificationExecutionRequest(BaseModel):
    status: str = Field(..., description="PASS, FAIL, or BLOCKED")
    evidence_summary: str = Field(..., description="Observed outcome / execution evidence")

class RiskCreate(BaseModel):
    id: str
    description: str
    likelihood: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)
    mitigation: str
    owner: Optional[str] = None
    status: str = "IDENTIFIED"

class RiskResponse(BaseModel):
    id: str
    description: str
    likelihood: int
    impact: int
    score: int
    mitigation: str
    owner: Optional[str] = None
    status: str
    review_date: Optional[datetime] = None

class DecisionCreate(BaseModel):
    id: str
    title: str
    context: str
    decision: str
    alternatives: str
    consequences: str
    status: str = "ACCEPTED"

class DecisionResponse(BaseModel):
    id: str
    title: str
    context: str
    decision: str
    alternatives: str
    consequences: str
    status: str
    date: datetime

class InterfaceCreate(BaseModel):
    id: str
    name: str
    producer: str
    consumer: str
    contract_spec: str
    version: str = "1.0.0"
    limitations: str

class InterfaceResponse(BaseModel):
    id: str
    name: str
    producer: str
    consumer: str
    contract_spec: str
    version: str
    limitations: str

class IssueCreate(BaseModel):
    id: str
    title: str
    description: str
    severity: str = "MAJOR"
    status: str = "OPEN"
    related_module: str
    resolution_notes: Optional[str] = None

class IssueResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    status: str
    related_module: str
    resolution_notes: Optional[str] = None

class ReadinessSummaryResponse(BaseModel):
    total_requirements: int
    verified_requirements: int
    unverified_requirements: int
    unlinked_requirements: int
    requirement_coverage_pct: float
    total_verification_cases: int
    cases_passed: int
    cases_failed: int
    cases_not_run: int
    cases_blocked: int
    open_risks_count: int
    critical_risks_count: int
    open_issues_count: int
    readiness_assessment: str
    disclaimer: str = "SIMULATION PORTFOLIO PROJECT READY FOR EDUCATIONAL / EVALUATION USE ONLY. NOT FLIGHT CERTIFIED."
