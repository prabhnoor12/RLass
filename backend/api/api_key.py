
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.api_key_manager import (
    issue_api_key_for_user, revoke_api_key, list_user_api_keys, get_api_key_details, validate_api_key, update_api_key_last_used, reactivate_api_key, count_api_keys
)
from ..schemas.api_key import APIKeyCreate, APIKeyRead
from ..database import get_db
from typing import List

router = APIRouter()

@router.post("/issue/{user_id}", response_model=APIKeyRead)
def issue_key(user_id: str, db: Session = Depends(get_db)):
    api_key = issue_api_key_for_user(db, user_id)
    return api_key

@router.post("/revoke/{key}")
def revoke_key(key: str, db: Session = Depends(get_db)):
    return {"success": revoke_api_key(db, key)}

@router.get("/user/{user_id}", response_model=List[APIKeyRead])
def list_keys(user_id: str, db: Session = Depends(get_db)):
    return list_user_api_keys(db, user_id)

@router.get("/details/{key}", response_model=APIKeyRead)
def key_details(key: str, db: Session = Depends(get_db)):
    api_key = get_api_key_details(db, key)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    return api_key

@router.get("/validate/{key}")
def validate_key(key: str, user_id: str = None, db: Session = Depends(get_db)):
    return {"valid": validate_api_key(db, key, user_id)}

@router.post("/reactivate/{key}")
def reactivate_key(key: str, db: Session = Depends(get_db)):
    return {"success": reactivate_api_key(db, key)}

@router.get("/count")
def count_keys(user_id: str = None, active_only: bool = False, db: Session = Depends(get_db)):
    return {"count": count_api_keys(db, user_id, active_only)}
