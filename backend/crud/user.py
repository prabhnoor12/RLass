from sqlalchemy.orm import Session, joinedload
from ..models.user import User
from ..schemas.user import UserCreate
from datetime import datetime
from typing import Optional, List
import uuid

def create_user(db: Session, user_in: UserCreate) -> User:
    """Create and store a new user in the database."""
    user_id = str(uuid.uuid4())
    db_user = User(
        id=user_id,
        email=user_in.email,
        hashed_password=user_in.password,  # Hash in real app!
        created_at=datetime.now(datetime.UTC),
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: str) -> Optional[User]:
    """Retrieve a user by their ID from the database."""
    # Eagerly load api_keys and audit_logs
    return db.query(User).filter(User.id == user_id).options(
        joinedload(User.api_keys),
        joinedload(User.audit_logs)
    ).first()

def update_user(db: Session, user_id: str, email: Optional[str] = None, password: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[User]:
    """Update user details in the database."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        if email:
            user.email = email
        if password:
            user.hashed_password = password  # Hash in real app!
        if is_active is not None:
            user.is_active = is_active
        db.commit()
        db.refresh(user)
        return user
    return None

def delete_user(db: Session, user_id: str) -> bool:
    """Delete a user by their ID from the database."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def list_users(db: Session, active_only: bool = False) -> List[User]:
    """List all users, optionally filtering only active users."""
    query = db.query(User).options(
        joinedload(User.api_keys),
        joinedload(User.audit_logs)
    )
    if active_only:
        query = query.filter(User.is_active == True)
    return query.all()
