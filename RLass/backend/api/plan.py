from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.plan_service import create_plan_with_check, get_plan, list_all_plans, update_plan_active_status, deactivate_plan, activate_plan
from ..schemas.plan import PlanCreate, PlanRead
from ..database import get_db
from typing import Optional

router = APIRouter()

@router.post("/create", response_model=PlanRead)
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    try:
        return create_plan_with_check(db, plan)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/get", response_model=PlanRead)
def get_plan_by_name(name: str, db: Session = Depends(get_db)):
    plan = get_plan(db, name)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.get("/list", response_model=list[PlanRead])
def list_plans(db: Session = Depends(get_db)):
    return list_all_plans(db)

@router.put("/activate/{plan_id}", response_model=PlanRead)
def activate(plan_id: int, db: Session = Depends(get_db)):
    plan = activate_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.put("/deactivate/{plan_id}", response_model=PlanRead)
def deactivate(plan_id: int, db: Session = Depends(get_db)):
    plan = deactivate_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan
