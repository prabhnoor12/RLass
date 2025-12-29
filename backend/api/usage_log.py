from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.usage_logger import log_usage_event, get_usage_events, delete_usage_events, count_usage_events, summarize_usage
from ..schemas.usage_log import UsageLogQuery
from ..database import get_db
from typing import Optional

router = APIRouter()

@router.post("/log")
def log_event(api_key: str, endpoint: Optional[str], identifier: str, status: str, db: Session = Depends(get_db)):
    return log_usage_event(db, api_key, endpoint, identifier, status)

@router.get("/events")
def usage_events(api_key: Optional[str] = None, endpoint: Optional[str] = None, identifier: Optional[str] = None, from_time: Optional[str] = None, to_time: Optional[str] = None, db: Session = Depends(get_db)):
    query = UsageLogQuery(api_key=api_key, endpoint=endpoint, identifier=identifier, from_time=from_time, to_time=to_time)
    return get_usage_events(db, query)

@router.delete("/events")
def delete_events(api_key: Optional[str] = None, identifier: Optional[str] = None, before: Optional[str] = None, db: Session = Depends(get_db)):
    return {"deleted": delete_usage_events(db, api_key, identifier, before)}

@router.get("/count")
def count_events(api_key: Optional[str] = None, endpoint: Optional[str] = None, identifier: Optional[str] = None, db: Session = Depends(get_db)):
    return {"count": count_usage_events(db, api_key, endpoint, identifier)}

@router.get("/summary")
def summary(group_by: str = "endpoint", api_key: Optional[str] = None, identifier: Optional[str] = None, db: Session = Depends(get_db)):
    return summarize_usage(db, group_by, api_key, identifier)
