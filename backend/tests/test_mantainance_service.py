import pytest
from backend.services import mantainance_service
from backend.schemas.maintenance import MaintenanceTaskCreate

def test_create_and_get_task(db_session):
    task_in = MaintenanceTaskCreate(name="backup")
    task = mantainance_service.create_task_with_check(db_session, task_in)
    assert task.name == "backup"
    fetched = mantainance_service.get_task(db_session, "backup")
    assert fetched is not None
    assert fetched.name == "backup"

def test_create_duplicate_task_raises(db_session):
    task_in = MaintenanceTaskCreate(name="dup")
    mantainance_service.create_task_with_check(db_session, task_in)
    with pytest.raises(ValueError):
        mantainance_service.create_task_with_check(db_session, task_in)

def test_list_tasks_and_update_status(db_session):
    task_in = MaintenanceTaskCreate(name="update-status")
    task = mantainance_service.create_task_with_check(db_session, task_in)
    tasks = mantainance_service.list_tasks(db_session)
    assert any(t.name == "update-status" for t in tasks)
    updated = mantainance_service.update_task_status(db_session, task.id, "done")
    assert updated.status == "done"

def test_run_and_deactivate_task(db_session):
    task_in = MaintenanceTaskCreate(name="run-task")
    task = mantainance_service.create_task_with_check(db_session, task_in)
    ran = mantainance_service.run_task(db_session, task.id)
    assert ran.status == "running"
    assert ran.last_run is not None
    deactivated = mantainance_service.deactivate_task(db_session, task.id)
    assert deactivated.is_active is False
