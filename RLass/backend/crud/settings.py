from sqlalchemy.orm import Session
from ..models.settings import UserSettings
from ..schemas.settings import UserSettingsCreate
from typing import Optional, List

def create_user_settings(db: Session, settings_in: UserSettingsCreate) -> UserSettings:
    db_settings = UserSettings(**settings_in.model_dump())
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings

def get_user_settings(db: Session, user_id: int) -> List[UserSettings]:
    return db.query(UserSettings).filter(UserSettings.user_id == user_id).all()

def update_user_settings(db: Session, user_id: int, key: str, value: str) -> Optional[UserSettings]:
    db_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id, UserSettings.key == key).first()
    if db_settings:
        db_settings.value = value
        db.commit()
        db.refresh(db_settings)
    return db_settings

def delete_user_settings(db: Session, user_id: int, key: str) -> int:
    deleted = db.query(UserSettings).filter(UserSettings.user_id == user_id, UserSettings.key == key).delete()
    db.commit()
    return deleted
