
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api import api_key
from backend.database import get_db

# Use the test db_session fixture from conftest.py

@pytest.fixture
def app(db_session):
    app = FastAPI()
    # Mount the API key router
    app.include_router(api_key.router, prefix="/api/key")
    # Override the get_db dependency to use the test session
    app.dependency_overrides[get_db] = lambda: db_session
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_issue_key(client, test_user):
    response = client.post(f"/api/key/issue/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user.id
    assert "key" in data

def test_list_keys(client, test_user):
    # Issue a key first
    client.post(f"/api/key/issue/{test_user.id}")
    response = client.get(f"/api/key/user/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(key["user_id"] == test_user.id for key in data)

def test_revoke_and_reactivate_key(client, test_user):
    # Issue a key
    issue_resp = client.post(f"/api/key/issue/{test_user.id}")
    key = issue_resp.json()["key"]
    # Revoke
    revoke_resp = client.post(f"/api/key/revoke/{key}")
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["success"] is True
    # Reactivate
    reactivate_resp = client.post(f"/api/key/reactivate/{key}")
    assert reactivate_resp.status_code == 200
    assert reactivate_resp.json()["success"] is True

def test_key_details_and_validate(client, test_user):
    issue_resp = client.post(f"/api/key/issue/{test_user.id}")
    key = issue_resp.json()["key"]
    # Details
    details_resp = client.get(f"/api/key/details/{key}")
    assert details_resp.status_code == 200
    details = details_resp.json()
    assert details["key"] == key
    # Validate
    validate_resp = client.get(f"/api/key/validate/{key}?user_id={test_user.id}")
    assert validate_resp.status_code == 200
    assert validate_resp.json()["valid"] is True

def test_count_keys(client, test_user):
    # Issue two keys
    client.post(f"/api/key/issue/{test_user.id}")
    client.post(f"/api/key/issue/{test_user.id}")
    count_resp = client.get(f"/api/key/count?user_id={test_user.id}")
    assert count_resp.status_code == 200
    assert count_resp.json()["count"] >= 2
