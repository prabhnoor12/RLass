from sqlalchemy.orm import Session
from ..models.plan import Plan
from ..schemas.plan import PlanCreate
from typing import Optional, List

def create_plan(db: Session, plan_in: PlanCreate) -> Plan:
    db_plan = Plan(**plan_in.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_plan_by_name(db: Session, name: str) -> Optional[Plan]:
    return db.query(Plan).filter(Plan.name == name).first()

def list_plans(db: Session) -> List[Plan]:
    return db.query(Plan).all()

def update_plan_status(db: Session, plan_id: int, is_active: bool) -> Optional[Plan]:
    db_plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if db_plan:
        db_plan.is_active = is_active
        db.commit()
        db.refresh(db_plan)
    return db_plan
