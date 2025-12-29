
from sqlalchemy.orm import Session, joinedload
from ..models.usage_log import UsageLog
from ..schemas.usage_log import UsageLogQuery
from datetime import datetime
from typing import Optional, List
import uuid

def log_usage(
    db: Session,
    api_key: str,
    endpoint: Optional[str],
    identifier: str,
    status: str
) -> UsageLog:
    """
    Log a usage event for an API key and identifier in the database.
    """
    entry = UsageLog(
        id=str(uuid.uuid4()),
        api_key=api_key,
        endpoint=endpoint,
        identifier=identifier,
        timestamp=datetime.utcnow(),
        status=status
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_usage_logs(db: Session, query: Optional[UsageLogQuery] = None) -> List[UsageLog]:
    """
    Retrieve usage logs from the database, optionally filtered by query parameters.
    """
    q = db.query(UsageLog).options(
        joinedload(UsageLog.api_key_obj)
    )
    if query:
        if query.api_key:
            q = q.filter(UsageLog.api_key == query.api_key)
        if query.endpoint:
            q = q.filter(UsageLog.endpoint == query.endpoint)
        if query.identifier:
            q = q.filter(UsageLog.identifier == query.identifier)
        if query.from_time:
            q = q.filter(UsageLog.timestamp >= query.from_time)
        if query.to_time:
            q = q.filter(UsageLog.timestamp <= query.to_time)
    return q.all()
