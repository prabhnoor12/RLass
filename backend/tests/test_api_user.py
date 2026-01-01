import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api import user
from backend.database import get_db

# Use the test db_session fixture from conftest.py

@pytest.fixture
def app(db_session):
    app = FastAPI()
    # Mount the user router
    app.include_router(user.router, prefix="/api/user")
    # Override the get_db dependency to use the test session
    app.dependency_overrides[get_db] = lambda: db_session
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_create_user(client):
    payload = {"email": "newuser@example.com", "password": "testpass"}
    response = client.post("/api/user/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["is_active"] is True
    assert "id" in data

def test_get_user(client):
    # First, create a user
    payload = {"email": "getuser@example.com", "password": "testpass"}
    create_resp = client.post("/api/user/create", json=payload)
    user_id = create_resp.json()["id"]
    # Now, get the user
    response = client.get(f"/api/user/get/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == payload["email"]

def test_update_user(client):
    # Create a user
    payload = {"email": "updateuser@example.com", "password": "testpass"}
    create_resp = client.post("/api/user/create", json=payload)
    user_id = create_resp.json()["id"]
    # Update the user
    update_payload = {"email": "updated@example.com", "password": "newpass", "is_active": False}
    response = client.put(f"/api/user/update/{user_id}", params=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == update_payload["email"]
    assert data["is_active"] is False
import pytest

# Add tests for backend/api/user.py here
def test_api_user_placeholder():
    assert True
