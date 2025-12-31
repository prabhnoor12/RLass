import pytest
from backend.services import user_manager
from backend.schemas.user import UserCreate

def test_create_and_get_user(db_session):
    user_in = UserCreate(email="new@example.com", password="pw")
    user = user_manager.create_user(db_session, user_in)
    assert user.email == "new@example.com"
    fetched = user_manager.get_user(db_session, user.id)
    assert fetched is not None
    assert fetched.email == "new@example.com"

def test_update_user(db_session, test_user):
    updated = user_manager.update_user(db_session, test_user.id, email="updated@example.com", is_active=False)
    assert updated.email == "updated@example.com"
    assert updated.is_active is False

def test_list_and_delete_user(db_session, test_user):
    users = user_manager.list_users(db_session)
    assert any(u.id == test_user.id for u in users)
    deleted = user_manager.delete_user(db_session, test_user.id)
    assert deleted is True
    assert user_manager.get_user(db_session, test_user.id) is None

def test_get_user_api_keys(db_session, test_user):
    from backend.crud.api_key import create_api_key
    from backend.schemas.api_key import APIKeyCreate
    api_key_obj = create_api_key(db_session, APIKeyCreate(user_id=test_user.id))
    keys = user_manager.get_user_api_keys(db_session, test_user.id)
    assert any(k.key == api_key_obj.key for k in keys)

def test_get_user_audit_logs(db_session, test_user):
    from backend.models.audit_log import AuditLog
    log = AuditLog(id="log1", actor_id=test_user.id, action="test", event_type="admin_action", target="tgt", timestamp=None, details=None)
    db_session.add(log)
    db_session.commit()
    logs = user_manager.get_user_audit_logs(db_session, test_user.id)
    assert any(l.id == "log1" for l in logs)
