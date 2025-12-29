from sqlalchemy.orm import Session
from ..models.maintenance import MaintenanceTask
from ..schemas.maintenance import MaintenanceTaskCreate
from typing import Optional, List

def create_maintenance_task(db: Session, task_in: MaintenanceTaskCreate) -> MaintenanceTask:
    db_task = MaintenanceTask(**task_in.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_maintenance_task(db: Session, name: str) -> Optional[MaintenanceTask]:
    return db.query(MaintenanceTask).filter(MaintenanceTask.name == name).first()

def list_maintenance_tasks(db: Session, is_active: Optional[bool] = None) -> List[MaintenanceTask]:
    q = db.query(MaintenanceTask)
    if is_active is not None:
        q = q.filter(MaintenanceTask.is_active == is_active)
    return q.all()

def update_maintenance_status(db: Session, task_id: int, status: str) -> Optional[MaintenanceTask]:
    db_task = db.query(MaintenanceTask).filter(MaintenanceTask.id == task_id).first()
    if db_task:
        db_task.status = status
        db.commit()
        db.refresh(db_task)
    return db_task
