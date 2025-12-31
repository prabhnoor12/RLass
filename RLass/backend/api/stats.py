from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.stats_service import list_stats, get_stats, increment_user_usage
from ..database import get_db
from typing import Optional

router = APIRouter()

@router.get("/list")
def stats_list(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    return list_stats(db, user_id)

@router.get("/get")
def stats_get(user_id: int, endpoint: str, period: str, db: Session = Depends(get_db)):
    return get_stats(db, user_id, endpoint, period)

@router.post("/increment")
def stats_increment(user_id: int, endpoint: str, period: str, db: Session = Depends(get_db)):
    return increment_user_usage(db, user_id, endpoint, period)
