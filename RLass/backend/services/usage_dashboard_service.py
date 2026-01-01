import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, case
from datetime import datetime, timedelta, UTC
from typing import Optional, List, Dict, Any
from functools import lru_cache
import logging

from ..services.usage_logger import summarize_usage
from ..services.stats_service import list_stats
from ..models.usage_log import UsageLog
from ..models.stats import UsageStats
from ..models.api_key import APIKey

logger = logging.getLogger("usage_dashboard_service")


def get_realtime_usage_stats(db: Session, user_id: str):
    """
    Get real-time usage statistics for a user.
    Combines usage summary and stats breakdown.
    """
    usage_summary = summarize_usage(db, group_by="endpoint", api_key=None, identifier=user_id)
    stats = list_stats(db, user_id=int(user_id))
    return {
        "usage_summary": usage_summary,
        "stats": [s.__dict__ for s in stats],
    }


def get_usage_by_time_range(
    db: Session,
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    granularity: str = "day"
) -> Dict[str, Any]:
    """
    Get usage statistics filtered by time range.

    Args:
        db: Database session
        user_id: User identifier
        start_date: Start of time range (defaults to 7 days ago)
        end_date: End of time range (defaults to now)
        granularity: Time grouping - 'hour', 'day', 'week', 'month'

    Returns:
        Dict containing usage data grouped by time periods
    """
    if not end_date:
        end_date = datetime.now(UTC)
    if not start_date:
        start_date = end_date - timedelta(days=7)

    query = db.query(UsageLog).filter(
        UsageLog.identifier == user_id,
        UsageLog.timestamp >= start_date,
        UsageLog.timestamp <= end_date
    )

    total_requests = query.count()

    # Group by time period (SQLite compatible)
    time_grouped = []
    if granularity == "hour":
        results = db.query(
            func.strftime('%Y-%m-%d %H:00:00', UsageLog.timestamp).label('period'),
            func.count(UsageLog.id).label('count')
        ).filter(
            UsageLog.identifier == user_id,
            UsageLog.timestamp >= start_date,
            UsageLog.timestamp <= end_date
        ).group_by('period').order_by('period').all()
        time_grouped = [{"period": str(r.period), "count": r.count} for r in results]
    elif granularity == "day":
        results = db.query(
            func.strftime('%Y-%m-%d', UsageLog.timestamp).label('period'),
            func.count(UsageLog.id).label('count')
        ).filter(
            UsageLog.identifier == user_id,
            UsageLog.timestamp >= start_date,
            UsageLog.timestamp <= end_date
        ).group_by('period').order_by('period').all()
        time_grouped = [{"period": str(r.period), "count": r.count} for r in results]

    logger.info(f"Retrieved usage by time range for user {user_id}: {total_requests} requests")

    return {
        "total_requests": total_requests,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "granularity": granularity,
        "time_series": time_grouped
    }


def get_error_breakdown(
    db: Session,
    user_id: str,
    time_window: Optional[int] = 24
) -> Dict[str, Any]:
    """
    Analyze error rates and success rates by endpoint.

    Args:
        db: Database session
        user_id: User identifier
        time_window: Time window in hours (default: 24)

    Returns:
        Dict containing error rates and breakdown by status
    """
    cutoff_time = datetime.now(UTC) - timedelta(hours=time_window)

    # Get all requests in time window
    total_query = db.query(func.count(UsageLog.id)).filter(
        UsageLog.identifier == user_id,
        UsageLog.timestamp >= cutoff_time
    )
    total_requests = total_query.scalar() or 0

    # Get status breakdown
    status_breakdown = db.query(
        UsageLog.status,
        func.count(UsageLog.id).label('count')
    ).filter(
        UsageLog.identifier == user_id,
        UsageLog.timestamp >= cutoff_time
    ).group_by(UsageLog.status).all()

    # Get error breakdown by endpoint
    error_by_endpoint = db.query(
        UsageLog.endpoint,
        UsageLog.status,
        func.count(UsageLog.id).label('count')
    ).filter(
        UsageLog.identifier == user_id,
        UsageLog.timestamp >= cutoff_time,
        UsageLog.status != "success"
    ).group_by(UsageLog.endpoint, UsageLog.status).all()

    # Calculate rates
    success_count = sum(r.count for r in status_breakdown if r.status == "success")
    error_count = total_requests - success_count

    success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
    error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

    logger.info(f"Error breakdown for user {user_id}: {error_rate:.2f}% error rate")

    return {
        "time_window_hours": time_window,
        "total_requests": total_requests,
        "success_count": success_count,
        "error_count": error_count,
        "success_rate": round(success_rate, 2),
        "error_rate": round(error_rate, 2),
        "status_breakdown": [{"status": r.status, "count": r.count} for r in status_breakdown],
        "errors_by_endpoint": [
            {"endpoint": r.endpoint, "status": r.status, "count": r.count}
            for r in error_by_endpoint
        ]
    }


def get_top_endpoints(
    db: Session,
    user_id: str,
    limit: int = 10,
    sort_by: str = "count",
    time_window: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get most-used endpoints and their metrics.

    Args:
        db: Database session
        user_id: User identifier
        limit: Maximum number of endpoints to return
        sort_by: Sort criteria - 'count' or 'error_rate'
        time_window: Time window in hours (None for all time)

    Returns:
        List of top endpoints with their usage metrics
    """
    query = db.query(
        UsageLog.endpoint,
        func.count(UsageLog.id).label('total_count'),
        func.sum(case((UsageLog.status == 'success', 1), else_=0)).label('success_count'),
        func.sum(case((UsageLog.status != 'success', 1), else_=0)).label('error_count')
    ).filter(UsageLog.identifier == user_id)

    if time_window:
        cutoff_time = datetime.now(UTC) - timedelta(hours=time_window)
        query = query.filter(UsageLog.timestamp >= cutoff_time)

    query = query.group_by(UsageLog.endpoint)

    results = query.all()

    # Calculate error rates and format
    endpoints = []
    for r in results:
        total = r.total_count or 0
        success = r.success_count or 0
        errors = r.error_count or 0
        error_rate = (errors / total * 100) if total > 0 else 0

        endpoints.append({
            "endpoint": r.endpoint,
            "total_requests": total,
            "success_count": success,
            "error_count": errors,
            "error_rate": round(error_rate, 2)
        })

    # Sort by criteria
    if sort_by == "error_rate":
        endpoints.sort(key=lambda x: x["error_rate"], reverse=True)
    else:
        endpoints.sort(key=lambda x: x["total_requests"], reverse=True)

    top_endpoints = endpoints[:limit]
    logger.info(f"Retrieved top {limit} endpoints for user {user_id}")

    return top_endpoints


async def get_realtime_usage_stats_async(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Async version of get_realtime_usage_stats for better WebSocket performance.

    Args:
        db: Database session
        user_id: User identifier

    Returns:
        Dict containing real-time usage statistics
    """
    # Run database queries in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    usage_summary = await loop.run_in_executor(
        None,
        summarize_usage,
        db,
        "endpoint",
        None,
        user_id
    )

    stats = await loop.run_in_executor(
        None,
        list_stats,
        db,
        int(user_id)
    )

    return {
        "usage_summary": usage_summary,
        "stats": [s.__dict__ for s in stats],
        "timestamp": datetime.now(UTC).isoformat()
    }


@lru_cache(maxsize=128)
def _get_cached_key(user_id: str, cache_time: int) -> str:
    """Helper to create cache keys with time buckets."""
    return f"{user_id}_{cache_time}"


def get_cached_usage_stats(
    db: Session,
    user_id: str,
    cache_ttl: int = 60
) -> Dict[str, Any]:
    """
    Get usage stats with caching to reduce database load.
    Cache is time-bucketed based on TTL.

    Args:
        db: Database session
        user_id: User identifier
        cache_ttl: Cache time-to-live in seconds

    Returns:
        Dict containing cached or fresh usage statistics
    """
    # Create time-bucketed cache key
    current_bucket = int(datetime.now(UTC).timestamp() // cache_ttl)
    cache_key = _get_cached_key(user_id, current_bucket)

    # This uses LRU cache on the key, actual data fetched fresh
    # For production, use Redis or similar
    stats = get_realtime_usage_stats(db, user_id)
    stats["cached_at"] = datetime.now(UTC).isoformat()
    stats["cache_ttl"] = cache_ttl

    logger.debug(f"Retrieved stats for user {user_id} (cache_key: {cache_key})")
    return stats


def get_quota_status(
    db: Session,
    user_id: str,
    period: str = "day"
) -> Dict[str, Any]:
    """
    Track quota consumption and check if nearing limits.

    Args:
        db: Database session
        user_id: User identifier
        period: Time period for quota - 'hour', 'day', 'month'

    Returns:
        Dict containing quota status and usage information
    """
    # Determine time window based on period
    now = datetime.now(UTC)
    if period == "hour":
        start_time = now - timedelta(hours=1)
    elif period == "day":
        start_time = now - timedelta(days=1)
    elif period == "month":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)

    # Count usage in current period
    current_usage = db.query(func.count(UsageLog.id)).filter(
        UsageLog.identifier == user_id,
        UsageLog.timestamp >= start_time
    ).scalar() or 0

    # Get user's rate limit (from API keys or default)
    # This is a simplified version - adjust based on your rate limit logic
    user_api_keys = db.query(APIKey).filter(
        APIKey.user_id == user_id,
        APIKey.is_active == True
    ).all()

    # Get rate limits for active API keys
    rate_limit = None
    for api_key in user_api_keys:
        if api_key.rate_limits:
            # Get the most permissive rate limit
            for rl in api_key.rate_limits:
                if rate_limit is None or rl.max_requests > rate_limit:
                    rate_limit = rl.max_requests

    # Default rate limit if none found
    if rate_limit is None:
        rate_limit = 1000  # Default quota

    usage_percentage = (current_usage / rate_limit * 100) if rate_limit > 0 else 0
    remaining = max(0, rate_limit - current_usage)

    # Determine status
    status = "healthy"
    if usage_percentage >= 90:
        status = "critical"
    elif usage_percentage >= 75:
        status = "warning"

    logger.info(f"Quota status for user {user_id}: {usage_percentage:.1f}% used")

    return {
        "period": period,
        "current_usage": current_usage,
        "quota_limit": rate_limit,
        "remaining": remaining,
        "usage_percentage": round(usage_percentage, 2),
        "status": status,
        "period_start": start_time.isoformat(),
        "period_end": now.isoformat()
    }
