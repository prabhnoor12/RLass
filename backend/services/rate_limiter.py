from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..crud import rate_limit as crud_rate_limit
from ..crud import usage_log as crud_usage_log
from ..crud import api_key as crud_api_key
from ..models.usage_log import UsageLog
from ..models.rate_limit import RateLimitConfig
from typing import Optional, Tuple


def check_and_log_rate_limit(
    db: Session,
    api_key: str,
    identifier: str,
    endpoint: Optional[str] = None,
    align_to_minute: bool = False
) -> Tuple[bool, int, int]:
    """
    Check if the API key/identifier is within the rate limit for the endpoint, log usage, and return (allowed, remaining, reset_timestamp).
    Supports endpoint-specific and global (all-endpoint) limits. Optionally aligns window to minute.
    """
    # Try endpoint-specific config first, then fallback to global config
    config = crud_rate_limit.get_rate_limit(db, api_key, endpoint)
    if not config and endpoint:
        config = crud_rate_limit.get_rate_limit(db, api_key, None)
    if not config:
        crud_usage_log.log_usage(db, api_key, endpoint, identifier, status="allowed")
        return True, -1, -1

    now = datetime.utcnow()
    if align_to_minute:
        window_start = now.replace(second=0, microsecond=0)
    else:
        window_start = now - timedelta(seconds=now.second % config.period_seconds, microseconds=now.microsecond)
    window_start_ts = int(window_start.timestamp())
    window_end_ts = window_start_ts + config.period_seconds

    from ..schemas.usage_log import UsageLogQuery
    usage_query = UsageLogQuery(
        api_key=api_key,
        endpoint=endpoint,
        identifier=identifier,
        from_time=datetime.utcfromtimestamp(window_start_ts),
        to_time=datetime.utcfromtimestamp(window_end_ts)
    )
    usage_count = len(crud_usage_log.get_usage_logs(db, usage_query))

    if usage_count < config.limit:
        crud_usage_log.log_usage(db, api_key, endpoint, identifier, status="allowed")
        allowed = True
    else:
        crud_usage_log.log_usage(db, api_key, endpoint, identifier, status="rate_limited")
        allowed = False

    remaining = max(0, config.limit - usage_count - (1 if allowed else 0))
    reset = window_end_ts
    return allowed, remaining, reset

def summarize_usage_for_api_key(
    db: Session,
    api_key: str,
    endpoint: Optional[str] = None,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None
) -> dict:
    """
    Summarize usage for an API key (optionally for an endpoint and time range).
    Returns a dict with total, allowed, and rate_limited counts.
    """
    from ..schemas.usage_log import UsageLogQuery
    usage_query = UsageLogQuery(
        api_key=api_key,
        endpoint=endpoint,
        from_time=from_time,
        to_time=to_time
    )
    logs = crud_usage_log.get_usage_logs(db, usage_query)
    total = len(logs)
    allowed = sum(1 for log in logs if log.status == "allowed")
    rate_limited = sum(1 for log in logs if log.status == "rate_limited")
    return {"total": total, "allowed": allowed, "rate_limited": rate_limited}

def reset_usage_logs_for_api_key(
    db: Session,
    api_key: str,
    endpoint: Optional[str] = None
) -> int:
    """
    Delete all usage logs for an API key (optionally for an endpoint). Useful for admin/testing.
    Returns the number of deleted logs.
    """
    from ..models.usage_log import UsageLog
    q = db.query(UsageLog).filter(UsageLog.api_key == api_key)
    if endpoint:
        q = q.filter(UsageLog.endpoint == endpoint)
    count = q.count()
    q.delete(synchronize_session=False)
    db.commit()
    return count

def get_rate_limit_config(db: Session, api_key: str, endpoint: Optional[str] = None) -> Optional[RateLimitConfig]:
    """
    Retrieve the rate limit configuration for a given API key and endpoint.
    """
    return crud_rate_limit.get_rate_limit(db, api_key, endpoint)
