from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.api_key_manager import (
    issue_api_key_for_user, revoke_api_key, list_user_api_keys, get_api_key_details, validate_api_key, update_api_key_last_used, reactivate_api_key, count_api_keys
)
from ..schemas.api_key import APIKeyCreate
from ..database import get_db

router = APIRouter()

@router.post("/issue/{user_id}")
def issue_key(user_id: str, db: Session = Depends(get_db)):
    return issue_api_key_for_user(db, user_id)

@router.post("/revoke/{key}")
def revoke_key(key: str, db: Session = Depends(get_db)):
    return {"success": revoke_api_key(db, key)}

@router.get("/user/{user_id}")
def list_keys(user_id: str, db: Session = Depends(get_db)):
    return list_user_api_keys(db, user_id)

@router.get("/details/{key}")
def key_details(key: str, db: Session = Depends(get_db)):
    return get_api_key_details(db, key)

@router.get("/validate/{key}")
def validate_key(key: str, user_id: str = None, db: Session = Depends(get_db)):
    return {"valid": validate_api_key(db, key, user_id)}

@router.post("/reactivate/{key}")
def reactivate_key(key: str, db: Session = Depends(get_db)):
    return {"success": reactivate_api_key(db, key)}

@router.get("/count")
def count_keys(user_id: str = None, active_only: bool = False, db: Session = Depends(get_db)):
    return {"count": count_api_keys(db, user_id, active_only)}
