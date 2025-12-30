
from sqlalchemy.orm import Session
from typing import Optional, List
from ..crud import maintenance as crud_maintenance
from ..models.maintenance import MaintenanceTask
from ..schemas.maintenance import MaintenanceTaskCreate, MaintenanceTaskRead
import logging
import datetime

logger = logging.getLogger("maintenance_service")

def create_task_with_check(db: Session, task_in: MaintenanceTaskCreate) -> MaintenanceTask:
	"""
	Create a new maintenance task if it does not already exist.
	Raises ValueError if task name already exists.
	"""
	existing = crud_maintenance.get_maintenance_task(db, task_in.name)
	if existing:
		logger.warning(f"Maintenance task '{task_in.name}' already exists.")
		raise ValueError(f"Maintenance task '{task_in.name}' already exists.")
	logger.info(f"Creating maintenance task: {task_in.name}")
	return crud_maintenance.create_maintenance_task(db, task_in)

def get_task(db: Session, name: str) -> Optional[MaintenanceTask]:
	"""
	Retrieve a maintenance task by name.
	"""
	return crud_maintenance.get_maintenance_task(db, name)

def list_tasks(db: Session, is_active: Optional[bool] = None) -> List[MaintenanceTask]:
	"""
	List all maintenance tasks, optionally filtered by active status.
	"""
	return crud_maintenance.list_maintenance_tasks(db, is_active)

def update_task_status(db: Session, task_id: int, status: str) -> Optional[MaintenanceTask]:
	"""
	Update the status of a maintenance task.
	"""
	logger.info(f"Updating maintenance task {task_id} to status '{status}'")
	return crud_maintenance.update_maintenance_status(db, task_id, status)

def run_task(db: Session, task_id: int) -> Optional[MaintenanceTask]:
	"""
	Mark a maintenance task as running, update last_run, and set status to 'running'.
	"""
	task = crud_maintenance.update_maintenance_status(db, task_id, "running")
	if task:
		task.last_run = datetime.datetime.now(datetime.UTC)
		db.commit()
		db.refresh(task)
		logger.info(f"Ran maintenance task {task_id}")
	else:
		logger.warning(f"Maintenance task {task_id} not found for running.")
	return task

def deactivate_task(db: Session, task_id: int) -> Optional[MaintenanceTask]:
	"""
	Deactivate a maintenance task (set is_active to False).
	"""
	task = db.query(MaintenanceTask).filter(MaintenanceTask.id == task_id).first()
	if task:
		task.is_active = False
		db.commit()
		db.refresh(task)
		logger.info(f"Deactivated maintenance task {task_id}")
	else:
		logger.warning(f"Maintenance task {task_id} not found for deactivation.")
	return task
