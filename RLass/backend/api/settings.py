from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.settings_service import create_settings_with_check, get_settings_for_user, update_settings_value, delete_settings, get_setting_value
from ..schemas.settings import UserSettingsCreate
from ..database import get_db
from typing import Optional

router = APIRouter()

@router.post("/create")
def create_settings(settings: UserSettingsCreate, db: Session = Depends(get_db)):
    try:
        return create_settings_with_check(db, settings)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/user/{user_id}")
def user_settings(user_id: int, db: Session = Depends(get_db)):
    return get_settings_for_user(db, user_id)

@router.put("/update")
def update_settings(user_id: int, key: str, value: str, db: Session = Depends(get_db)):
    return update_settings_value(db, user_id, key, value)

@router.delete("/delete")
def delete_setting(user_id: int, key: str, db: Session = Depends(get_db)):
    return {"deleted": delete_settings(db, user_id, key)}

@router.get("/get")
def get_setting(user_id: int, key: str, db: Session = Depends(get_db)):
    return {"value": get_setting_value(db, user_id, key)}
