import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import CommandRecord
from app.schemas.command import CommandCreateRequest, CommandResponse, CommandStatus, CommandType
from app.services.command_service import CommandService
from app.services.simulation_engine import simulator

router = APIRouter(prefix="/v1/commands", tags=["Command Centre"])

@router.get("", response_model=List[CommandResponse])
def get_commands(
    run_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(CommandRecord)
    effective_run_id = run_id or simulator.active_run_id
    if effective_run_id:
        query = query.filter(CommandRecord.run_id == effective_run_id)
    records = query.order_by(CommandRecord.created_at.desc()).offset(offset).limit(limit).all()

    res = []
    for r in records:
        params = json.loads(r.parameters_json) if r.parameters_json else {}
        result = json.loads(r.result_json) if r.result_json else None
        res.append(
            CommandResponse(
                id=r.id,
                run_id=r.run_id,
                idempotency_key=r.idempotency_key,
                command_type=CommandType(r.command_type),
                parameters=params,
                issued_by=r.issued_by,
                status=CommandStatus(r.status),
                rejection_reason=r.rejection_reason,
                result=result,
                created_at=r.created_at,
                executed_at=r.executed_at,
            )
        )
    return res

@router.get("/{command_id}", response_model=CommandResponse)
def get_command_by_id(command_id: str, db: Session = Depends(get_db)):
    r = db.query(CommandRecord).filter(CommandRecord.id == command_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Command '{command_id}' not found.")

    params = json.loads(r.parameters_json) if r.parameters_json else {}
    result = json.loads(r.result_json) if r.result_json else None
    return CommandResponse(
        id=r.id,
        run_id=r.run_id,
        idempotency_key=r.idempotency_key,
        command_type=CommandType(r.command_type),
        parameters=params,
        issued_by=r.issued_by,
        status=CommandStatus(r.status),
        rejection_reason=r.rejection_reason,
        result=result,
        created_at=r.created_at,
        executed_at=r.executed_at,
    )

@router.post("", response_model=CommandResponse)
def submit_command(req: CommandCreateRequest, db: Session = Depends(get_db)):
    cmd_record = CommandService.submit_command(db=db, request=req)
    params = json.loads(cmd_record.parameters_json) if cmd_record.parameters_json else {}
    result = json.loads(cmd_record.result_json) if cmd_record.result_json else None
    return CommandResponse(
        id=cmd_record.id,
        run_id=cmd_record.run_id,
        idempotency_key=cmd_record.idempotency_key,
        command_type=CommandType(cmd_record.command_type),
        parameters=params,
        issued_by=cmd_record.issued_by,
        status=CommandStatus(cmd_record.status),
        rejection_reason=cmd_record.rejection_reason,
        result=result,
        created_at=cmd_record.created_at,
        executed_at=cmd_record.executed_at,
    )
