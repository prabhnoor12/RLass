from sqlalchemy.orm import Session
from ..models.auth import AuthToken
from ..schemas.auth import AuthTokenCreate
from typing import Optional
from datetime import datetime, UTC

def create_auth_token(db: Session, token_in: AuthTokenCreate) -> AuthToken:
    db_token = AuthToken(**token_in.model_dump())
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def get_auth_token(db: Session, token: str) -> Optional[AuthToken]:
    return db.query(AuthToken).filter(AuthToken.token == token).first()

def deactivate_auth_token(db: Session, token: str) -> Optional[AuthToken]:
    db_token = get_auth_token(db, token)
    if db_token:
        db_token.is_active = False
        db.commit()
        db.refresh(db_token)
    return db_token

def delete_expired_tokens(db: Session) -> int:
    now = datetime.now(UTC)
    deleted = db.query(AuthToken).filter(AuthToken.expires_at < now).delete()
    db.commit()
    return deleted
