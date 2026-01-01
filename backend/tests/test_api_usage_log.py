
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    from backend.database import get_db
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_log_event(client, test_user):
    # Log a usage event
    response = client.post("/usage-log/log", params={
        "api_key": "key1",
        "endpoint": "/endpoint1",
        "identifier": str(test_user.id),
        "status": "allowed"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["api_key"] == "key1"
    assert data["endpoint"] == "/endpoint1"
    assert data["identifier"] == str(test_user.id)
    assert data["status"] == "allowed"


def test_usage_events(client, usage_log):
    # Get usage events
    response = client.get("/usage-log/events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(log["id"] == "log1" for log in data)

    # Filter by api_key
    response = client.get("/usage-log/events", params={"api_key": "key1"})
    assert response.status_code == 200
    data = response.json()
    assert all(log["api_key"] == "key1" for log in data)


def test_delete_events(client, usage_log):
    # Delete usage events by api_key
    response = client.delete("/usage-log/events", params={"api_key": "key1"})
    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data
    assert data["deleted"] >= 1


def test_count_events(client, usage_log):
    # Count usage events
    response = client.get("/usage-log/count", params={"api_key": "key1"})
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert data["count"] >= 1


def test_summary(client, usage_log):
    # Get usage summary grouped by endpoint
    response = client.get("/usage-log/summary", params={"group_by": "endpoint"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any("endpoint" in item and "count" in item for item in data)
