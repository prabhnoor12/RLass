
from sqlalchemy.orm import Session
from ..crud import auth as crud_auth
from ..schemas.auth import AuthTokenCreate
from ..models.auth import AuthToken
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger("auth_service")

def issue_token(db: Session, token_in: AuthTokenCreate) -> AuthToken:
    """
    Issue a new auth token after performing any necessary business checks.
    Extend here to check user status, prevent duplicate tokens, or log issuance.
    """
    # Example: log token issuance
    logger.info(f"Issuing token for user_id={token_in.user_id}")
    return crud_auth.create_auth_token(db, token_in)

def validate_token(db: Session, token: str, check_expiry: bool = True) -> Optional[AuthToken]:
    """
    Validate a token: must be active and (optionally) not expired.
    Returns the AuthToken if valid, else None.
    """
    db_token = crud_auth.get_auth_token(db, token)
    if not db_token:
        logger.warning(f"Token not found: {token}")
        return None
    if not db_token.is_active:
        logger.info(f"Token inactive: {token}")
        return None
    if check_expiry and db_token.expires_at < datetime.utcnow():
        logger.info(f"Token expired: {token}")
        return None
    return db_token

def revoke_token(db: Session, token: str) -> Optional[AuthToken]:
    """
    Revoke (deactivate) a token. Returns the updated AuthToken or None.
    """
    logger.info(f"Revoking token: {token}")
    return crud_auth.deactivate_auth_token(db, token)

def cleanup_expired_tokens(db: Session) -> int:
    """
    Delete all expired tokens from the database. Returns the number deleted.
    """
    deleted = crud_auth.delete_expired_tokens(db)
    logger.info(f"Cleaned up {deleted} expired tokens.")
    return deleted
