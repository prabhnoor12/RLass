from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.plan_service import create_plan_with_check, get_plan, list_all_plans, update_plan_active_status, deactivate_plan, activate_plan
from ..schemas.plan import PlanCreate
from ..database import get_db
from typing import Optional

router = APIRouter()

@router.post("/create")
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    return create_plan_with_check(db, plan)

@router.get("/get")
def get_plan_by_name(name: str, db: Session = Depends(get_db)):
    return get_plan(db, name)

@router.get("/list")
def list_plans(db: Session = Depends(get_db)):
    return list_all_plans(db)

@router.put("/activate/{plan_id}")
def activate(plan_id: int, db: Session = Depends(get_db)):
    return activate_plan(db, plan_id)

@router.put("/deactivate/{plan_id}")
def deactivate(plan_id: int, db: Session = Depends(get_db)):
    return deactivate_plan(db, plan_id)
