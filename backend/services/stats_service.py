
from sqlalchemy.orm import Session
from typing import Optional, List
from ..crud import stats as crud_stats
from ..models.stats import UsageStats
from ..schemas.stats import UsageStatsCreate, UsageStatsRead
import logging

logger = logging.getLogger("stats_service")

def create_stats_with_check(db: Session, stats_in: UsageStatsCreate) -> UsageStats:
	"""
	Create a new usage stats entry if it does not already exist for the user/endpoint/period.
	Raises ValueError if already exists.
	"""
	existing = crud_stats.get_usage_stats(db, stats_in.user_id, stats_in.endpoint, stats_in.period)
	if existing:
		logger.warning(f"Usage stats for user {stats_in.user_id}, endpoint '{stats_in.endpoint}', period '{stats_in.period}' already exist.")
		raise ValueError(f"Usage stats for user {stats_in.user_id}, endpoint '{stats_in.endpoint}', period '{stats_in.period}' already exist.")
	logger.info(f"Creating usage stats for user {stats_in.user_id}, endpoint: {stats_in.endpoint}, period: {stats_in.period}")
	return crud_stats.create_usage_stats(db, stats_in)

def get_stats(db: Session, user_id: int, endpoint: str, period: str) -> Optional[UsageStats]:
	"""
	Retrieve usage stats for a user, endpoint, and period.
	"""
	return crud_stats.get_usage_stats(db, user_id, endpoint, period)

def list_stats(db: Session, user_id: Optional[int] = None) -> List[UsageStats]:
	"""
	List all usage stats, optionally filtered by user.
	"""
	return crud_stats.list_usage_stats(db, user_id)

def increment_user_usage(db: Session, user_id: int, endpoint: str, period: str) -> UsageStats:
	"""
	Increment the usage count for a user/endpoint/period.
	"""
	logger.info(f"Incrementing usage for user {user_id}, endpoint: {endpoint}, period: {period}")
	return crud_stats.increment_usage(db, user_id, endpoint, period)
