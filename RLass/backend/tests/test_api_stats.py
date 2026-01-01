
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.stats import UsageStats

@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    # Patch get_db to use the test session
    from backend.database import get_db
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_stats_list(client, usage_stats, test_user):
    # Test listing all stats
    response = client.get(f"/stats/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(stat["user_id"] == int(test_user.id) for stat in data)

    # Test filtering by user_id
    response = client.get(f"/stats/list?user_id={test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert all(stat["user_id"] == int(test_user.id) for stat in data)


def test_stats_get(client, usage_stats, test_user):
    # Test getting stats for specific user/endpoint/period
    response = client.get(f"/stats/get?user_id={test_user.id}&endpoint=/endpoint1&period=day")
    assert response.status_code == 200
    stat = response.json()
    assert stat["user_id"] == int(test_user.id)
    assert stat["endpoint"] == "/endpoint1"
    assert stat["period"] == "day"
    assert stat["count"] == 5

    # Test not found case
    response = client.get(f"/stats/get?user_id=999&endpoint=notfound&period=day")
    assert response.status_code == 200
    assert response.json() is None


def test_stats_increment(client, test_user):
    # Increment usage for a new stat
    response = client.post(f"/stats/increment?user_id={test_user.id}&endpoint=/endpoint2&period=day")
    assert response.status_code == 200
    stat = response.json()
    assert stat["user_id"] == int(test_user.id)
    assert stat["endpoint"] == "/endpoint2"
    assert stat["period"] == "day"
    assert stat["count"] == 1

    # Increment usage for an existing stat
    response = client.post(f"/stats/increment?user_id={test_user.id}&endpoint=/endpoint2&period=day")
    assert response.status_code == 200
    stat = response.json()
    assert stat["count"] == 2
