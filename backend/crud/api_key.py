
from sqlalchemy.orm import Session, joinedload
from ..models.api_key import APIKey
from ..schemas.api_key import APIKeyCreate
import datetime
from typing import Optional, List
import uuid

def create_api_key(db: Session, api_key_in: APIKeyCreate) -> APIKey:
    """Create and store a new API key for a user in the database."""
    key = str(uuid.uuid4())
    db_api_key = APIKey(
        key=key,
        user_id=api_key_in.user_id,
        is_active=True,
        created_at=datetime.datetime.now(datetime.UTC),
        last_used=None
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

def get_api_key(db: Session, key: str) -> Optional[APIKey]:
    """Retrieve an API key by its value from the database."""
    # Eagerly load user, rate_limits, and usage_logs
    return db.query(APIKey).filter(APIKey.key == key).options(
        joinedload(APIKey.user),
        joinedload(APIKey.rate_limits),
        joinedload(APIKey.usage_logs)
    ).first()

def revoke_api_key(db: Session, key: str) -> bool:
    """Deactivate (revoke) an API key in the database."""
    api_key = db.query(APIKey).filter(APIKey.key == key).first()
    if api_key:
        api_key.is_active = False
        db.commit()
        return True
    return False

def list_api_keys(db: Session, user_id: Optional[str] = None) -> List[APIKey]:
    """List all API keys, optionally filtered by user_id, from the database."""
    query = db.query(APIKey).options(
        joinedload(APIKey.user),
        joinedload(APIKey.rate_limits),
        joinedload(APIKey.usage_logs)
    )
    if user_id:
        query = query.filter(APIKey.user_id == user_id)
    return query.all()

def update_last_used(db: Session, key: str) -> None:
    """Update the last_used timestamp for an API key in the database."""
    api_key = db.query(APIKey).filter(APIKey.key == key).first()
    if api_key:
        api_key.last_used = datetime.datetime.now(datetime.UTC)
        db.commit()
