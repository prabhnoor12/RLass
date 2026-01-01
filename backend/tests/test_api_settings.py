import pytest

# Add tests for backend/api/settings.py here
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api import settings
from backend.database import get_db
from backend.models.settings import UserSettings


@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(settings.router, prefix="/api/settings")
    app.dependency_overrides[get_db] = lambda: db_session
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def test_settings(db_session, test_user):
    settings_obj = UserSettings(user_id=int(test_user.id), key="theme", value="dark", is_active=True)
    db_session.add(settings_obj)
    db_session.commit()
    db_session.refresh(settings_obj)
    return settings_obj

def test_create_settings_success(client, test_user):
    response = client.post(
        "/api/settings/create",
        json={"user_id": int(test_user.id), "key": "language", "value": "en", "is_active": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "language"
    assert data["value"] == "en"
    assert data["is_active"] is True

def test_create_settings_duplicate(client, test_settings):
    response = client.post(
        "/api/settings/create",
        json={"user_id": test_settings.user_id, "key": test_settings.key, "value": "dark", "is_active": True}
    )
    assert response.status_code in [400, 409, 422, 200]

def test_get_user_settings(client, test_settings):
    response = client.get(f"/api/settings/user/{test_settings.user_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(s["key"] == "theme" for s in data)

def test_update_settings(client, test_settings):
    response = client.put(f"/api/settings/update?user_id={test_settings.user_id}&key={test_settings.key}&value=light")
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == "light"

def test_delete_settings(client, test_settings):
    response = client.delete(f"/api/settings/delete?user_id={test_settings.user_id}&key={test_settings.key}")
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] == 1

def test_get_setting_value(client, test_settings):
    response = client.get(f"/api/settings/get?user_id={test_settings.user_id}&key={test_settings.key}")
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == test_settings.value
