import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from backend.services import auth_service
from backend.crud import auth as crud_auth
from backend.schemas.auth import AuthTokenCreate


def test_issue_token(db_session, token_data):
    token_in = AuthTokenCreate(**token_data)
    token = auth_service.issue_token(db_session, token_in)
    assert token.token == token_data["token"]
    assert token.is_active
    assert token.user_id == token_data["user_id"]


def test_validate_token_valid(db_session, token_data):
    token_in = AuthTokenCreate(**token_data)
    token = auth_service.issue_token(db_session, token_in)
    validated = auth_service.validate_token(db_session, token.token)
    assert validated is not None
    assert validated.token == token.token


def test_validate_token_expired(db_session, token_data):
    token_data["expires_at"] = datetime.now(UTC) - timedelta(hours=1)
    token_in = AuthTokenCreate(**token_data)
    token = auth_service.issue_token(db_session, token_in)
    validated = auth_service.validate_token(db_session, token.token)
    assert validated is None


def test_revoke_token(db_session, token_data):
    token_in = AuthTokenCreate(**token_data)
    token = auth_service.issue_token(db_session, token_in)
    revoked = auth_service.revoke_token(db_session, token.token)
    assert not revoked.is_active
    validated = auth_service.validate_token(db_session, token.token)
    assert validated is None


def test_cleanup_expired_tokens(db_session, token_data):
    # Create one expired and one valid token
    expired_data = token_data.copy()
    expired_data["token"] = "expiredtoken"
    expired_data["expires_at"] = datetime.now(UTC) - timedelta(hours=1)
    valid_data = token_data.copy()
    valid_data["token"] = "validtoken"
    valid_data["expires_at"] = datetime.now(UTC) + timedelta(hours=1)
    auth_service.issue_token(db_session, AuthTokenCreate(**expired_data))
    auth_service.issue_token(db_session, AuthTokenCreate(**valid_data))
    deleted = auth_service.cleanup_expired_tokens(db_session)
    assert deleted == 1
    assert crud_auth.get_auth_token(db_session, "expiredtoken") is None
    assert crud_auth.get_auth_token(db_session, "validtoken") is not None
