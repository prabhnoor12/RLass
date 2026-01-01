from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.mantainance_service import create_task_with_check, get_task, list_tasks, update_task_status, run_task, deactivate_task
from ..schemas.maintenance import MaintenanceTaskCreate
from ..database import get_db
from typing import Optional

router = APIRouter()

@router.post("/create")
def create_task(task: MaintenanceTaskCreate, db: Session = Depends(get_db)):
    try:
        return create_task_with_check(db, task)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/get")
def get_task_by_name(name: str, db: Session = Depends(get_db)):
    return get_task(db, name)

@router.get("/list")
def list_all_tasks(is_active: Optional[bool] = None, db: Session = Depends(get_db)):
    return list_tasks(db, is_active)

@router.put("/update-status/{task_id}")
def update_status(task_id: int, status: str, db: Session = Depends(get_db)):
    return update_task_status(db, task_id, status)

@router.post("/run/{task_id}")
def run(task_id: int, db: Session = Depends(get_db)):
    return run_task(db, task_id)

@router.put("/deactivate/{task_id}")
def deactivate(task_id: int, db: Session = Depends(get_db)):
    return deactivate_task(db, task_id)
