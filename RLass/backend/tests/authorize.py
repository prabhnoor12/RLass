import pytest
from datetime import datetime, timedelta, UTC
from backend.crud import auth as crud_auth
from backend.schemas.auth import AuthTokenCreate


def test_create_auth_token(db_session, token_data):
    token_in = AuthTokenCreate(**token_data)
    token = crud_auth.create_auth_token(db_session, token_in)
    assert token.token == token_data["token"]
    assert token.is_active
    assert token.user_id == token_data["user_id"]


def test_get_auth_token(db_session, token_data):
    token_in = AuthTokenCreate(**token_data)
    crud_auth.create_auth_token(db_session, token_in)
    token = crud_auth.get_auth_token(db_session, token_data["token"])
    assert token is not None
    assert token.token == token_data["token"]


def test_deactivate_auth_token(db_session, token_data):
    token_in = AuthTokenCreate(**token_data)
    crud_auth.create_auth_token(db_session, token_in)
    token = crud_auth.deactivate_auth_token(db_session, token_data["token"])
    assert token is not None
    assert not token.is_active


def test_delete_expired_tokens(db_session, token_data):
    expired_data = token_data.copy()
    expired_data["token"] = "expiredtoken"
    expired_data["expires_at"] = datetime.now(UTC) - timedelta(hours=1)
    valid_data = token_data.copy()
    valid_data["token"] = "validtoken"
    valid_data["expires_at"] = datetime.now(UTC) + timedelta(hours=1)
    crud_auth.create_auth_token(db_session, AuthTokenCreate(**expired_data))
    crud_auth.create_auth_token(db_session, AuthTokenCreate(**valid_data))
    deleted = crud_auth.delete_expired_tokens(db_session)
    assert deleted == 1
    assert crud_auth.get_auth_token(db_session, "expiredtoken") is None
    assert crud_auth.get_auth_token(db_session, "validtoken") is not None
