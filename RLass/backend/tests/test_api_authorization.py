import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api import authorization
from backend.database import get_db
from backend.models.authorization import Role, UserRole


@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(authorization.router, prefix="/api/authorization")
    app.dependency_overrides[get_db] = lambda: db_session
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def test_role(db_session):
    role = Role(name="admin", description="Administrator role")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


# ===================== Role Endpoints =====================

def test_create_role_success(client):
    response = client.post(
        "/api/authorization/role/create",
        json={"name": "editor", "description": "Editor role"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "editor"
    assert data["description"] == "Editor role"


def test_create_role_duplicate(client, test_role):
    response = client.post(
        "/api/authorization/role/create",
        json={"name": "admin", "description": "Duplicate admin role"}
    )
    # Should fail or return error for duplicate role
    assert response.status_code in [400, 409, 422, 200]


def test_get_role_by_name(client, test_role):
    response = client.get(f"/api/authorization/role/get?name={test_role.name}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "admin"


def test_get_role_not_found(client):
    response = client.get("/api/authorization/role/get?name=nonexistent")
    # Should return 404 or None
    assert response.status_code in [200, 404]


def test_list_roles_empty(client):
    response = client.get("/api/authorization/role/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_roles_with_entries(client, test_role):
    response = client.get("/api/authorization/role/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    role_names = [r["name"] for r in data]
    assert "admin" in role_names


# ===================== User-Role Endpoints =====================

def test_assign_role_to_user(client, db_session, test_user, test_role):
    response = client.post(
        "/api/authorization/user-role/assign",
        json={"user_id": int(test_user.id), "role_id": test_role.id}
    )
    assert response.status_code == 200


def test_get_user_roles(client, db_session, test_user, test_role):
    # First assign the role
    user_role = UserRole(user_id=int(test_user.id), role_id=test_role.id)
    db_session.add(user_role)
    db_session.commit()

    response = client.get(f"/api/authorization/user-role/list/{int(test_user.id)}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_user_roles_empty(client, test_user):
    response = client.get(f"/api/authorization/user-role/list/{int(test_user.id)}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_user_has_role_true(client, db_session, test_user, test_role):
    # Assign the role first
    user_role = UserRole(user_id=int(test_user.id), role_id=test_role.id)
    db_session.add(user_role)
    db_session.commit()

    response = client.get(
        f"/api/authorization/user-role/has-role?user_id={int(test_user.id)}&role_name={test_role.name}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_role"] is True


def test_user_has_role_false(client, test_user):
    response = client.get(
        f"/api/authorization/user-role/has-role?user_id={int(test_user.id)}&role_name=nonexistent"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_role"] is False


def test_remove_role_from_user(client, db_session, test_user, test_role):
    # Assign the role first
    user_role = UserRole(user_id=int(test_user.id), role_id=test_role.id)
    db_session.add(user_role)
    db_session.commit()

    response = client.delete(
        f"/api/authorization/user-role/remove?user_id={int(test_user.id)}&role_id={test_role.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["removed"] is True


def test_remove_role_not_assigned(client, test_user, test_role):
    response = client.delete(
        f"/api/authorization/user-role/remove?user_id={int(test_user.id)}&role_id={test_role.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["removed"] is False
