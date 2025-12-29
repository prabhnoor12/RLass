
from sqlalchemy.orm import Session
from ..crud import api_key as crud_api_key
from ..crud import user as crud_user
from ..schemas.api_key import APIKeyCreate
from ..models.api_key import APIKey
from ..models.user import User
from typing import List, Optional
import logging

logger = logging.getLogger("api_key_manager")

def issue_api_key_for_user(db: Session, user_id: str) -> APIKey:
	"""
	Issue a new API key for a given user. Raises ValueError if user not found.
	"""
	user = crud_user.get_user(db, user_id)
	if not user:
		logger.error(f"User not found: {user_id}")
		raise ValueError("User not found")
	api_key_in = APIKeyCreate(user_id=user_id)
	api_key = crud_api_key.create_api_key(db, api_key_in)
	logger.info(f"Issued new API key for user {user_id}")
	return api_key

def revoke_api_key(db: Session, key: str) -> bool:
	"""
	Revoke (deactivate) an API key. Returns True if successful.
	"""
	result = crud_api_key.revoke_api_key(db, key)
	if result:
		logger.info(f"Revoked API key: {key}")
	else:
		logger.warning(f"API key not found for revocation: {key}")
	return result

def list_user_api_keys(db: Session, user_id: str) -> List[APIKey]:
	"""
	List all API keys for a given user.
	"""
	keys = crud_api_key.list_api_keys(db, user_id=user_id)
	logger.info(f"Listed {len(keys)} API keys for user {user_id}")
	return keys

def get_api_key_details(db: Session, key: str) -> Optional[APIKey]:
	"""
	Get details for a specific API key, including user and related info.
	"""
	api_key = crud_api_key.get_api_key(db, key)
	if api_key:
		logger.info(f"Fetched API key details for {key}")
	else:
		logger.warning(f"API key not found: {key}")
	return api_key

def validate_api_key(db: Session, key: str, user_id: Optional[str] = None) -> bool:
	"""
	Validate that an API key exists, is active, and (optionally) belongs to a given user.
	"""
	api_key = crud_api_key.get_api_key(db, key)
	if not api_key or not api_key.is_active:
		logger.warning(f"API key invalid or inactive: {key}")
		return False
	if user_id and api_key.user_id != user_id:
		logger.warning(f"API key {key} does not belong to user {user_id}")
		return False
	logger.info(f"API key {key} validated for user {user_id}")
	return True

def update_api_key_last_used(db: Session, key: str) -> None:
	"""
	Update the last_used timestamp for an API key.
	"""
	crud_api_key.update_last_used(db, key)
	logger.info(f"Updated last_used for API key {key}")

def reactivate_api_key(db: Session, key: str) -> bool:
	"""
	Reactivate a previously deactivated API key. Returns True if successful.
	"""
	api_key = crud_api_key.get_api_key(db, key)
	if api_key and not api_key.is_active:
		api_key.is_active = True
		db.commit()
		logger.info(f"Reactivated API key {key}")
		return True
	logger.warning(f"API key {key} not found or already active")
	return False

def count_api_keys(db: Session, user_id: Optional[str] = None, active_only: bool = False) -> int:
	"""
	Count API keys, optionally filtered by user and active status.
	"""
	q = db.query(APIKey)
	if user_id:
		q = q.filter(APIKey.user_id == user_id)
	if active_only:
		q = q.filter(APIKey.is_active == True)
	count = q.count()
	logger.info(f"Counted {count} API keys (user_id={user_id}, active_only={active_only})")
	return count
