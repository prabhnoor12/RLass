import pytest




from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api import audit_log
from backend.database import get_db

@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(audit_log.router, prefix="/api/audit")
    app.dependency_overrides[get_db] = lambda: db_session
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_export_audit_logs_empty(client):
    response = client.get("/api/audit/logs/export")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 0

def test_export_audit_logs_with_entry(client, db_session, test_user):
    from backend.services.audit import log_audit_event
    log_audit_event(
        db_session,
        action="login",
        actor_id=test_user.id,
        target="system",
        details="User logged in",
        event_type="auth"
    )
    response = client.get(f"/api/audit/logs/export?actor_id={test_user.id}&action=login")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1
    log = data["data"][0]
    assert log["actor_id"] == test_user.id
    assert log["action"] == "login"
