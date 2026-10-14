import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.mission_plan import (
    MissionTaskCreate,
    MissionTaskUpdate,
    MissionTaskResponse,
    ScheduleGenerateResponse,
)
from app.services.mission_planning_service import MissionPlanningService

router = APIRouter(prefix="/v1", tags=["Mission Planning"])

@router.get("/tasks", response_model=List[MissionTaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    tasks = MissionPlanningService.get_tasks(db)
    return [MissionPlanningService._to_response(t) for t in tasks]

@router.post("/tasks", response_model=MissionTaskResponse)
def create_task(task_in: MissionTaskCreate, db: Session = Depends(get_db)):
    try:
        task = MissionPlanningService.create_task(db, task_in)
        return MissionPlanningService._to_response(task)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/tasks/{task_id}", response_model=MissionTaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = MissionPlanningService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")
    return MissionPlanningService._to_response(task)

@router.put("/tasks/{task_id}", response_model=MissionTaskResponse)
def update_task(task_id: str, task_in: MissionTaskUpdate, db: Session = Depends(get_db)):
    try:
        task = MissionPlanningService.update_task(db, task_id, task_in)
        return MissionPlanningService._to_response(task)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    try:
        MissionPlanningService.delete_task(db, task_id)
        return {"success": True, "deleted_task_id": task_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/schedules/generate", response_model=ScheduleGenerateResponse)
def generate_schedule(db: Session = Depends(get_db)):
    return MissionPlanningService.generate_schedule(db)

@router.get("/schedules/current", response_model=ScheduleGenerateResponse)
def get_current_schedule(db: Session = Depends(get_db)):
    return MissionPlanningService.generate_schedule(db)
