from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.systems_eng import (
    RequirementResponse,
    VerificationCaseResponse,
    VerificationExecutionRequest,
    RiskResponse,
    DecisionResponse,
    InterfaceResponse,
    IssueResponse,
    ReadinessSummaryResponse,
)
from app.services.systems_engineering_service import SystemsEngineeringService
from app.services.report_service import ReportService
from app.db.models import RiskRecord, DesignDecisionRecord, InterfaceRecord, IssueRecord

router = APIRouter(prefix="/v1/systems-engineering", tags=["Systems Engineering"])

@router.get("/requirements", response_model=List[RequirementResponse])
def get_requirements(db: Session = Depends(get_db)):
    return SystemsEngineeringService.get_requirements(db)

@router.get("/verification-cases", response_model=List[VerificationCaseResponse])
def get_verification_cases(db: Session = Depends(get_db)):
    return SystemsEngineeringService.get_verification_cases(db)

@router.post("/verification-cases/{case_id}/execute", response_model=VerificationCaseResponse)
def execute_verification_case(
    case_id: str, req: VerificationExecutionRequest, db: Session = Depends(get_db)
):
    try:
        rec = SystemsEngineeringService.record_verification_result(
            db=db, case_id=case_id, status=req.status, evidence=req.evidence_summary
        )
        cases = SystemsEngineeringService.get_verification_cases(db)
        match = next(c for c in cases if c.id == rec.id)
        return match
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/risks", response_model=List[RiskResponse])
def get_risks(db: Session = Depends(get_db)):
    SystemsEngineeringService.seed_initial_records(db)
    risks = db.query(RiskRecord).all()
    return [
        RiskResponse(
            id=r.id,
            description=r.description,
            likelihood=r.likelihood,
            impact=r.impact,
            score=r.score,
            mitigation=r.mitigation,
            owner=r.owner,
            status=r.status,
            review_date=r.review_date,
        )
        for r in risks
    ]

@router.get("/decisions", response_model=List[DecisionResponse])
def get_decisions(db: Session = Depends(get_db)):
    SystemsEngineeringService.seed_initial_records(db)
    decs = db.query(DesignDecisionRecord).all()
    return [
        DecisionResponse(
            id=d.id,
            title=d.title,
            context=d.context,
            decision=d.decision,
            alternatives=d.alternatives,
            consequences=d.consequences,
            status=d.status,
            date=d.date,
        )
        for d in decs
    ]

@router.get("/interfaces", response_model=List[InterfaceResponse])
def get_interfaces(db: Session = Depends(get_db)):
    SystemsEngineeringService.seed_initial_records(db)
    ifaces = db.query(InterfaceRecord).all()
    return [
        InterfaceResponse(
            id=i.id,
            name=i.name,
            producer=i.producer,
            consumer=i.consumer,
            contract_spec=i.contract_spec,
            version=i.version,
            limitations=i.limitations,
        )
        for i in ifaces
    ]

@router.get("/issues", response_model=List[IssueResponse])
def get_issues(db: Session = Depends(get_db)):
    SystemsEngineeringService.seed_initial_records(db)
    issues = db.query(IssueRecord).all()
    return [
        IssueResponse(
            id=i.id,
            title=i.title,
            description=i.description,
            severity=i.severity,
            status=i.status,
            related_module=i.related_module,
            resolution_notes=i.resolution_notes,
        )
        for i in issues
    ]

@router.get("/readiness", response_model=ReadinessSummaryResponse)
def get_readiness(db: Session = Depends(get_db)):
    return SystemsEngineeringService.get_readiness_summary(db)

@router.get("/traceability/csv")
def get_traceability_csv(db: Session = Depends(get_db)):
    csv_str = ReportService.export_traceability_matrix_csv(db)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aurora_traceability_matrix.csv"},
    )
