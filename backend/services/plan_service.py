
from sqlalchemy.orm import Session
from typing import Optional, List
from ..crud import plan as crud_plan
from ..models.plan import Plan
from ..schemas.plan import PlanCreate, PlanRead
import logging

logger = logging.getLogger("plan_service")

def create_plan_with_check(db: Session, plan_in: PlanCreate) -> Plan:
	"""
	Create a new plan if it does not already exist.
	Raises ValueError if plan name already exists.
	"""
	existing = crud_plan.get_plan_by_name(db, plan_in.name)
	if existing:
		logger.warning(f"Plan '{plan_in.name}' already exists.")
		raise ValueError(f"Plan '{plan_in.name}' already exists.")
	logger.info(f"Creating plan: {plan_in.name}")
	return crud_plan.create_plan(db, plan_in)

def get_plan(db: Session, name: str) -> Optional[Plan]:
	"""
	Retrieve a plan by name.
	"""
	return crud_plan.get_plan_by_name(db, name)

def list_all_plans(db: Session) -> List[Plan]:
	"""
	List all plans in the system.
	"""
	return crud_plan.list_plans(db)

def update_plan_active_status(db: Session, plan_id: int, is_active: bool) -> Optional[Plan]:
	"""
	Update the active status of a plan.
	"""
	logger.info(f"Updating plan {plan_id} active status to {is_active}")
	return crud_plan.update_plan_status(db, plan_id, is_active)

def deactivate_plan(db: Session, plan_id: int) -> Optional[Plan]:
	"""
	Deactivate a plan (set is_active to False).
	"""
	return update_plan_active_status(db, plan_id, False)

def activate_plan(db: Session, plan_id: int) -> Optional[Plan]:
	"""
	Activate a plan (set is_active to True).
	"""
	return update_plan_active_status(db, plan_id, True)
