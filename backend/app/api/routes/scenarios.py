import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ScenarioRunRecord
from app.schemas.scenario import ScenarioDefinitionResponse, ScenarioRunResponse
from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/v1", tags=["Scenario Lab"])

@router.get("/scenarios", response_model=List[ScenarioDefinitionResponse])
def get_scenarios(db: Session = Depends(get_db)):
    scs = ScenarioService.get_scenarios(db)
    return [
        ScenarioDefinitionResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            seed=s.seed,
            initial_config=json.loads(s.initial_config_json),
            fault_schedule=json.loads(s.fault_schedule_json),
            expected_outcomes=json.loads(s.expected_outcomes_json),
            version=s.version,
        )
        for s in scs
    ]

@router.get("/scenarios/{scenario_id}", response_model=ScenarioDefinitionResponse)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    s = ScenarioService.get_scenario(db, scenario_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scenario '{scenario_id}' not found.")
    return ScenarioDefinitionResponse(
        id=s.id,
        name=s.name,
        description=s.description,
        seed=s.seed,
        initial_config=json.loads(s.initial_config_json),
        fault_schedule=json.loads(s.fault_schedule_json),
        expected_outcomes=json.loads(s.expected_outcomes_json),
        version=s.version,
    )

@router.post("/scenarios/{scenario_id}/run", response_model=ScenarioRunResponse)
def run_scenario(scenario_id: str, db: Session = Depends(get_db)):
    try:
        return ScenarioService.run_scenario(db, scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/scenario-runs", response_model=List[ScenarioRunResponse])
def get_scenario_runs(db: Session = Depends(get_db)):
    runs = db.query(ScenarioRunRecord).order_by(ScenarioRunRecord.started_at.desc()).limit(100).all()
    res = []
    for r in runs:
        observed = json.loads(r.observed_outcomes_json) if r.observed_outcomes_json else None
        deviations = json.loads(r.deviations_json) if r.deviations_json else None
        res.append(
            ScenarioRunResponse(
                id=r.id,
                scenario_id=r.scenario_id,
                run_id=r.run_id,
                status=r.status,
                seed=r.seed,
                observed_outcomes=observed,
                pass_fail=r.pass_fail,
                deviations=deviations,
                started_at=r.started_at,
                completed_at=r.completed_at,
            )
        )
    return res
