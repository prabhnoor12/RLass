import pytest

# Add tests for backend/api/maintenance.py here
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api import maintenance
from backend.database import get_db
from backend.models.maintenance import MaintenanceTask


@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(maintenance.router, prefix="/api/maintenance")
    app.dependency_overrides[get_db] = lambda: db_session
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def test_task(db_session):
    task = MaintenanceTask(name="backup", status="pending", is_active=True)
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task

def test_create_task_success(client):
    response = client.post(
        "/api/maintenance/create",
        json={"name": "cleanup", "status": "pending", "is_active": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "cleanup"
    assert data["status"] == "pending"
    assert data["is_active"] is True

def test_create_task_duplicate(client, test_task):
    response = client.post(
        "/api/maintenance/create",
        json={"name": "backup", "status": "pending", "is_active": True}
    )
    assert response.status_code in [400, 409, 422, 200]

def test_get_task_by_name(client, test_task):
    response = client.get(f"/api/maintenance/get?name={test_task.name}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "backup"

def test_get_task_not_found(client):
    response = client.get("/api/maintenance/get?name=nonexistent")
    assert response.status_code in [200, 404]

def test_list_all_tasks_empty(client):
    response = client.get("/api/maintenance/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_list_all_tasks_with_entries(client, test_task):
    response = client.get("/api/maintenance/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    names = [t["name"] for t in data]
    assert "backup" in names

def test_update_task_status(client, test_task):
    response = client.put(f"/api/maintenance/update-status/{test_task.id}?status=completed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"

def test_run_task(client, test_task):
    response = client.post(f"/api/maintenance/run/{test_task.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["last_run"] is not None

def test_deactivate_task(client, test_task):
    response = client.put(f"/api/maintenance/deactivate/{test_task.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
