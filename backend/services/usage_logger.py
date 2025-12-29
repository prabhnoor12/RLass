
from sqlalchemy.orm import Session
from ..crud import usage_log as crud_usage_log
from ..schemas.usage_log import UsageLogQuery
from ..models.usage_log import UsageLog
from typing import List, Optional
import logging
from datetime import datetime

logger = logging.getLogger("usage_logger")

def log_usage_event(db: Session, api_key: str, endpoint: Optional[str], identifier: str, status: str) -> UsageLog:
	"""
	Log a usage event for an API key and identifier. Returns the created UsageLog.
	Raises Exception if logging fails.
	"""
	try:
		log = crud_usage_log.log_usage(db, api_key, endpoint, identifier, status)
		logger.info(f"Logged usage event: api_key={api_key}, endpoint={endpoint}, identifier={identifier}, status={status}")
		return log
	except Exception as e:
		logger.error(f"Failed to log usage event: {e}")
		raise

def get_usage_events(db: Session, query: Optional[UsageLogQuery] = None) -> List[UsageLog]:
	"""
	Retrieve usage logs, optionally filtered by query parameters.
	"""
	return crud_usage_log.get_usage_logs(db, query)

def delete_usage_events(db: Session, api_key: Optional[str] = None, identifier: Optional[str] = None, before: Optional[datetime] = None) -> int:
	"""
	Delete usage logs by api_key, identifier, or before a certain timestamp. Returns number deleted.
	"""
	q = db.query(UsageLog)
	if api_key:
		q = q.filter(UsageLog.api_key == api_key)
	if identifier:
		q = q.filter(UsageLog.identifier == identifier)
	if before:
		q = q.filter(UsageLog.timestamp < before)
	count = q.delete()
	db.commit()
	logger.info(f"Deleted {count} usage logs (api_key={api_key}, identifier={identifier}, before={before})")
	return count

def count_usage_events(db: Session, api_key: Optional[str] = None, endpoint: Optional[str] = None, identifier: Optional[str] = None) -> int:
	"""
	Count usage logs by api_key, endpoint, or identifier.
	"""
	q = db.query(UsageLog)
	if api_key:
		q = q.filter(UsageLog.api_key == api_key)
	if endpoint:
		q = q.filter(UsageLog.endpoint == endpoint)
	if identifier:
		q = q.filter(UsageLog.identifier == identifier)
	count = q.count()
	logger.info(f"Counted {count} usage logs (api_key={api_key}, endpoint={endpoint}, identifier={identifier})")
	return count

def summarize_usage(db: Session, group_by: str = "endpoint", api_key: Optional[str] = None, identifier: Optional[str] = None) -> List[dict]:
	"""
	Aggregate usage logs, grouped by a field (default: endpoint). Returns a list of dicts with group and count.
	"""
	from sqlalchemy import func
	q = db.query(getattr(UsageLog, group_by), func.count(UsageLog.id)).group_by(getattr(UsageLog, group_by))
	if api_key:
		q = q.filter(UsageLog.api_key == api_key)
	if identifier:
		q = q.filter(UsageLog.identifier == identifier)
	results = q.all()
	summary = [{group_by: r[0], "count": r[1]} for r in results]
	logger.info(f"Usage summary by {group_by}: {summary}")
	return summary
