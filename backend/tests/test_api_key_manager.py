import pytest

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api import api_key
from backend.database import get_db
from backend.models.api_key import APIKey


@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(api_key.router, prefix="/api/api_key")
    app.dependency_overrides[get_db] = lambda: db_session
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_issue_api_key(client, test_user):
    response = client.post(f"/api/api_key/issue/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["is_active"] is True
    assert "key" in data

def test_issue_api_key_invalid_user(client):
    response = client.post("/api/api_key/issue/invalid_user")
    assert response.status_code in [400, 404, 422, 500]

def test_list_user_api_keys(client, test_user):
    # Issue two keys
    client.post(f"/api/api_key/issue/{test_user.id}")
    client.post(f"/api/api_key/issue/{test_user.id}")
    response = client.get(f"/api/api_key/user/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    for key in data:
        assert key["user_id"] == test_user.id

def test_get_api_key_details(client, test_user):
    issue_resp = client.post(f"/api/api_key/issue/{test_user.id}")
    key = issue_resp.json()["key"]
    response = client.get(f"/api/api_key/details/{key}")
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == key
    assert data["user_id"] == test_user.id

def test_get_api_key_details_not_found(client):
    response = client.get("/api/api_key/details/nonexistentkey")
    assert response.status_code == 404

def test_validate_api_key(client, test_user):
    issue_resp = client.post(f"/api/api_key/issue/{test_user.id}")
    key = issue_resp.json()["key"]
    response = client.get(f"/api/api_key/validate/{key}?user_id={test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True

def test_validate_api_key_invalid(client):
    response = client.get("/api/api_key/validate/invalidkey?user_id=invalid_user")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False

def test_revoke_api_key(client, test_user):
    issue_resp = client.post(f"/api/api_key/issue/{test_user.id}")
    key = issue_resp.json()["key"]
    response = client.post(f"/api/api_key/revoke/{key}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Validate should now be False
    response = client.get(f"/api/api_key/validate/{key}?user_id={test_user.id}")
    assert response.json()["valid"] is False

def test_revoke_api_key_not_found(client):
    response = client.post("/api/api_key/revoke/nonexistentkey")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False

def test_reactivate_api_key(client, test_user):
    issue_resp = client.post(f"/api/api_key/issue/{test_user.id}")
    key = issue_resp.json()["key"]
    # Revoke first
    client.post(f"/api/api_key/revoke/{key}")
    # Reactivate
    response = client.post(f"/api/api_key/reactivate/{key}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Validate should now be True
    response = client.get(f"/api/api_key/validate/{key}?user_id={test_user.id}")
    assert response.json()["valid"] is True

def test_count_api_keys(client, test_user):
    # Issue two keys
    client.post(f"/api/api_key/issue/{test_user.id}")
    client.post(f"/api/api_key/issue/{test_user.id}")
    response = client.get(f"/api/api_key/count?user_id={test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert data["count"] >= 2
