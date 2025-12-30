import asyncio
from sqlalchemy.orm import Session
from ..services.usage_logger import summarize_usage
from ..services.stats_service import list_stats

def get_realtime_usage_stats(db: Session, user_id: str):
    # Example: combine usage summary and stats breakdown
    usage_summary = summarize_usage(db, group_by="endpoint", api_key=None, identifier=user_id)
    stats = list_stats(db, user_id=int(user_id))
    # You can add more breakdowns (by error type, time window, etc.)
    return {
        "usage_summary": usage_summary,
        "stats": [s.__dict__ for s in stats],
    }
