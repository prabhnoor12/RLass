from sqlalchemy.orm import Session
from ..crud import user as crud_user
from ..crud import api_key as crud_api_key
from ..crud import audit_log as crud_audit_log
from ..schemas.user import UserCreate
from ..models.user import User
from ..models.api_key import APIKey
from ..models.audit_log import AuditLog
from typing import List, Optional

def create_user(db: Session, user_in: UserCreate) -> User:
	"""
	Create a new user in the system.
	"""
	user = crud_user.create_user(db, user_in)
	# Audit log for user creation (admin action)
	from ..services.audit import log_audit_event
	log_audit_event(db, action="create_user", actor_id="admin", target=user.id, event_type="admin_action")
	return user

def update_user(db: Session, user_id: str, email: Optional[str] = None, password: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[User]:
	"""
	Update user details.
	"""
	user = crud_user.update_user(db, user_id, email, password, is_active)
	# Audit log for user update (admin action)
	from ..services.audit import log_audit_event
	log_audit_event(db, action="update_user", actor_id="admin", target=user_id, event_type="admin_action")
	return user

def delete_user(db: Session, user_id: str) -> bool:
	"""
	Delete a user from the system.
	"""
	return crud_user.delete_user(db, user_id)

def get_user(db: Session, user_id: str) -> Optional[User]:
	"""
	Retrieve a user by ID, including API keys and audit logs.
	"""
	return crud_user.get_user(db, user_id)

def list_users(db: Session, active_only: bool = False) -> List[User]:
	"""
	List all users, optionally filtering only active users.
	"""
	return crud_user.list_users(db, active_only)

def get_user_api_keys(db: Session, user_id: str) -> List[APIKey]:
	"""
	Get all API keys for a user.
	"""
	return crud_api_key.list_api_keys(db, user_id=user_id)

def get_user_audit_logs(db: Session, user_id: str) -> List[AuditLog]:
	"""
	Get all audit logs for a user (as actor).
	"""
	from ..schemas.audit_log import AuditLogQuery
	query = AuditLogQuery(actor_id=user_id)
	return crud_audit_log.get_audit_logs(db, query)
