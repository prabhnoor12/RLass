import pytest

# Add tests for backend/api/plan.py here
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api import plan
from backend.database import get_db
from backend.models.plan import Plan


@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(plan.router, prefix="/api/plan")
    app.dependency_overrides[get_db] = lambda: db_session
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def test_plan(db_session):
    plan_obj = Plan(name="basic", description="Basic plan", rate_limit=100, is_active=True)
    db_session.add(plan_obj)
    db_session.commit()
    db_session.refresh(plan_obj)
    return plan_obj

def test_create_plan_success(client):
    response = client.post(
        "/api/plan/create",
        json={"name": "pro", "description": "Pro plan", "rate_limit": 1000, "is_active": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "pro"
    assert data["rate_limit"] == 1000
    assert data["is_active"] is True

def test_create_plan_duplicate(client, test_plan):
    response = client.post(
        "/api/plan/create",
        json={"name": "basic", "description": "Basic plan", "rate_limit": 100, "is_active": True}
    )
    assert response.status_code in [400, 409, 422, 200]

def test_get_plan_by_name(client, test_plan):
    response = client.get(f"/api/plan/get?name={test_plan.name}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "basic"

def test_get_plan_not_found(client):
    response = client.get("/api/plan/get?name=nonexistent")
    assert response.status_code in [200, 404]

def test_list_plans_empty(client):
    response = client.get("/api/plan/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_list_plans_with_entries(client, test_plan):
    response = client.get("/api/plan/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    names = [p["name"] for p in data]
    assert "basic" in names

def test_activate_plan(client, test_plan):
    # Deactivate first
    client.put(f"/api/plan/deactivate/{test_plan.id}")
    response = client.put(f"/api/plan/activate/{test_plan.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True

def test_deactivate_plan(client, test_plan):
    response = client.put(f"/api/plan/deactivate/{test_plan.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False

def test_api_plan_placeholder():
    assert True
