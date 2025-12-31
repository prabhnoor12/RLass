from sqlalchemy.orm import Session
from ..models.stats import UsageStats
from ..schemas.stats import UsageStatsCreate
from typing import Optional, List

def create_usage_stats(db: Session, stats_in: UsageStatsCreate) -> UsageStats:
    db_stats = UsageStats(**stats_in.model_dump())
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    return db_stats

def get_usage_stats(db: Session, user_id: int, endpoint: str, period: str) -> Optional[UsageStats]:
    return db.query(UsageStats).filter(UsageStats.user_id == user_id, UsageStats.endpoint == endpoint, UsageStats.period == period).first()

def list_usage_stats(db: Session, user_id: Optional[int] = None) -> List[UsageStats]:
    q = db.query(UsageStats)
    if user_id:
        q = q.filter(UsageStats.user_id == user_id)
    return q.all()

def increment_usage(db: Session, user_id: int, endpoint: str, period: str) -> UsageStats:
    stats = get_usage_stats(db, user_id, endpoint, period)
    if stats:
        stats.count += 1
    else:
        stats = UsageStats(user_id=user_id, endpoint=endpoint, period=period, count=1)
        db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats
