
from sqlalchemy.orm import Session
from typing import Optional, List
from ..crud import settings as crud_settings
from ..models.settings import UserSettings
from ..schemas.settings import UserSettingsCreate, UserSettingsRead
import logging

logger = logging.getLogger("settings_service")

def create_settings_with_check(db: Session, settings_in: UserSettingsCreate) -> UserSettings:
	"""
	Create a new user settings entry if it does not already exist for the key.
	Raises ValueError if the key already exists for the user.
	"""
	existing = db.query(UserSettings).filter(UserSettings.user_id == settings_in.user_id, UserSettings.key == settings_in.key).first()
	if existing:
		logger.warning(f"Settings for user {settings_in.user_id} and key '{settings_in.key}' already exist.")
		raise ValueError(f"Settings for user {settings_in.user_id} and key '{settings_in.key}' already exist.")
	logger.info(f"Creating settings for user {settings_in.user_id}, key: {settings_in.key}")
	return crud_settings.create_user_settings(db, settings_in)

def get_settings_for_user(db: Session, user_id: int) -> List[UserSettings]:
	"""
	Retrieve all settings for a user.
	"""
	return crud_settings.get_user_settings(db, user_id)

def update_settings_value(db: Session, user_id: int, key: str, value: str) -> Optional[UserSettings]:
	"""
	Update the value of a user's settings key.
	"""
	logger.info(f"Updating settings for user {user_id}, key: {key}")
	return crud_settings.update_user_settings(db, user_id, key, value)

def delete_settings(db: Session, user_id: int, key: str) -> int:
	"""
	Delete a user's settings key.
	"""
	logger.info(f"Deleting settings for user {user_id}, key: {key}")
	return crud_settings.delete_user_settings(db, user_id, key)

def get_setting_value(db: Session, user_id: int, key: str) -> Optional[str]:
	"""
	Get the value for a specific user's settings key.
	"""
	settings = db.query(UserSettings).filter(UserSettings.user_id == user_id, UserSettings.key == key).first()
	return settings.value if settings else None
