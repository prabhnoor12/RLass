
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from ..crud import usage_log as crud_usage_log
from ..schemas.usage_log import UsageLogQuery
from ..models.usage_log import UsageLog
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta, UTC
from collections import defaultdict

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


# ============================================================================
# Feature 1: Batch Logging
# ============================================================================

def batch_log_usage_events(
	db: Session,
	events: List[Dict[str, Any]]
) -> List[UsageLog]:
	"""
	Log multiple usage events in a single transaction for better performance.
	
	Args:
		db: Database session
		events: List of dicts with 'api_key', 'endpoint', 'identifier', 'status', and optional 'customer_id'
	
	Returns:
		List of created UsageLog objects
	
	Example:
		events = [
			{'api_key': 'key1', 'endpoint': '/api/v1/users', 'identifier': 'user1', 'status': 'success'},
			{'api_key': 'key1', 'endpoint': '/api/v1/posts', 'identifier': 'user1', 'status': 'error'},
		]
	"""
	logs = []
	
	try:
		for event in events:
			log = crud_usage_log.log_usage(
				db,
				api_key=event['api_key'],
				endpoint=event.get('endpoint'),
				identifier=event['identifier'],
				status=event['status'],
				customer_id=event.get('customer_id')
			)
			logs.append(log)
		
		logger.info(f"Batch logged {len(logs)} usage events")
		return logs
		
	except Exception as e:
		db.rollback()
		logger.error(f"Batch logging failed: {e}")
		raise


def log_usage_with_retry(
	db: Session,
	api_key: str,
	endpoint: Optional[str],
	identifier: str,
	status: str,
	max_retries: int = 3
) -> Optional[UsageLog]:
	"""
	Log a usage event with automatic retry on failure.
	
	Args:
		db: Database session
		api_key: API key
		endpoint: Endpoint being accessed
		identifier: User/request identifier
		status: Status of the request
		max_retries: Maximum number of retry attempts
	
	Returns:
		UsageLog object or None if all retries failed
	"""
	for attempt in range(max_retries):
		try:
			log = crud_usage_log.log_usage(db, api_key, endpoint, identifier, status)
			logger.info(f"Logged usage event on attempt {attempt + 1}")
			return log
		except Exception as e:
			logger.warning(f"Failed to log usage (attempt {attempt + 1}/{max_retries}): {e}")
			if attempt == max_retries - 1:
				logger.error(f"Failed to log usage after {max_retries} attempts")
				return None
			db.rollback()
	
	return None


# ============================================================================
# Feature 2: Advanced Filtering & Search
# ============================================================================

def get_usage_events_filtered(
	db: Session,
	api_key: Optional[str] = None,
	endpoint: Optional[str] = None,
	identifier: Optional[str] = None,
	status: Optional[str] = None,
	customer_id: Optional[str] = None,
	start_time: Optional[datetime] = None,
	end_time: Optional[datetime] = None,
	limit: Optional[int] = None,
	offset: int = 0,
	order_by: str = "timestamp",
	order_desc: bool = True
) -> Dict[str, Any]:
	"""
	Advanced filtering with pagination and sorting.
	
	Args:
		db: Database session
		api_key: Filter by API key
		endpoint: Filter by endpoint
		identifier: Filter by identifier
		status: Filter by status
		customer_id: Filter by customer ID
		start_time: Start of time range
		end_time: End of time range
		limit: Maximum number of results
		offset: Number of results to skip
		order_by: Field to order by
		order_desc: Order descending if True
	
	Returns:
		Dict with 'logs', 'total', 'limit', 'offset'
	"""
	query = db.query(UsageLog)
	
	# Apply filters
	if api_key:
		query = query.filter(UsageLog.api_key == api_key)
	if endpoint:
		query = query.filter(UsageLog.endpoint == endpoint)
	if identifier:
		query = query.filter(UsageLog.identifier == identifier)
	if status:
		query = query.filter(UsageLog.status == status)
	if customer_id:
		query = query.filter(UsageLog.customer_id == customer_id)
	if start_time:
		query = query.filter(UsageLog.timestamp >= start_time)
	if end_time:
		query = query.filter(UsageLog.timestamp <= end_time)
	
	# Count total before pagination
	total = query.count()
	
	# Apply ordering
	order_field = getattr(UsageLog, order_by, UsageLog.timestamp)
	if order_desc:
		query = query.order_by(desc(order_field))
	else:
		query = query.order_by(order_field)
	
	# Apply pagination
	if limit:
		query = query.limit(limit)
	query = query.offset(offset)
	
	logs = query.all()
	
	logger.info(f"Filtered usage events: {len(logs)} of {total} total")
	
	return {
		'logs': logs,
		'total': total,
		'limit': limit,
		'offset': offset,
		'has_more': total > (offset + len(logs))
	}


def search_usage_logs(
	db: Session,
	search_term: str,
	search_fields: List[str] = ['endpoint', 'identifier', 'api_key'],
	limit: int = 100
) -> List[UsageLog]:
	"""
	Search usage logs across multiple fields.
	
	Args:
		db: Database session
		search_term: Term to search for
		search_fields: Fields to search in
		limit: Maximum results
	
	Returns:
		List of matching UsageLog objects
	"""
	filters = []
	for field in search_fields:
		if hasattr(UsageLog, field):
			filters.append(getattr(UsageLog, field).ilike(f"%{search_term}%"))
	
	if not filters:
		return []
	
	query = db.query(UsageLog).filter(or_(*filters)).limit(limit)
	results = query.all()
	
	logger.info(f"Search for '{search_term}' returned {len(results)} results")
	
	return results


# ============================================================================
# Feature 3: Time-Series Analysis
# ============================================================================

def get_usage_time_series(
	db: Session,
	identifier: Optional[str] = None,
	api_key: Optional[str] = None,
	endpoint: Optional[str] = None,
	start_time: Optional[datetime] = None,
	end_time: Optional[datetime] = None,
	interval: str = "hour"
) -> List[Dict[str, Any]]:
	"""
	Get usage data grouped by time intervals.
	
	Args:
		db: Database session
		identifier: Optional identifier filter
		api_key: Optional API key filter
		endpoint: Optional endpoint filter
		start_time: Start of time range
		end_time: End of time range
		interval: Time interval - 'minute', 'hour', 'day', 'week', 'month'
	
	Returns:
		List of time-series data points with timestamp and count
	"""
	if not end_time:
		end_time = datetime.now(UTC)
	if not start_time:
		start_time = end_time - timedelta(days=7)
	
	# Map interval to SQL function
	interval_map = {
		'minute': 'minute',
		'hour': 'hour',
		'day': 'day',
		'week': 'week',
		'month': 'month'
	}
	
	trunc_interval = interval_map.get(interval, 'hour')
	
	query = db.query(
		func.date_trunc(trunc_interval, UsageLog.timestamp).label('time_bucket'),
		func.count(UsageLog.id).label('count')
	).filter(
		UsageLog.timestamp >= start_time,
		UsageLog.timestamp <= end_time
	)
	
	if identifier:
		query = query.filter(UsageLog.identifier == identifier)
	if api_key:
		query = query.filter(UsageLog.api_key == api_key)
	if endpoint:
		query = query.filter(UsageLog.endpoint == endpoint)
	
	query = query.group_by('time_bucket').order_by('time_bucket')
	
	results = query.all()
	
	time_series = [
		{
			'timestamp': r.time_bucket.isoformat() if r.time_bucket else None,
			'count': r.count
		}
		for r in results
	]
	
	logger.info(f"Generated time series with {len(time_series)} data points ({interval} interval)")
	
	return time_series


def get_hourly_distribution(
	db: Session,
	identifier: Optional[str] = None,
	days_back: int = 7
) -> Dict[int, int]:
	"""
	Get usage distribution by hour of day (0-23).
	Useful for understanding peak usage times.
	
	Args:
		db: Database session
		identifier: Optional identifier filter
		days_back: Number of days to analyze
	
	Returns:
		Dict mapping hour (0-23) to request count
	"""
	start_time = datetime.now(UTC) - timedelta(days=days_back)
	
	query = db.query(
		func.extract('hour', UsageLog.timestamp).label('hour'),
		func.count(UsageLog.id).label('count')
	).filter(UsageLog.timestamp >= start_time)
	
	if identifier:
		query = query.filter(UsageLog.identifier == identifier)
	
	query = query.group_by('hour').order_by('hour')
	
	results = query.all()
	
	# Initialize all hours with 0
	distribution = {hour: 0 for hour in range(24)}
	
	# Fill in actual counts
	for r in results:
		if r.hour is not None:
			distribution[int(r.hour)] = r.count
	
	logger.info(f"Hourly distribution calculated for {days_back} days")
	
	return distribution


# ============================================================================
# Feature 4: Status & Error Analysis
# ============================================================================

def get_status_breakdown(
	db: Session,
	identifier: Optional[str] = None,
	api_key: Optional[str] = None,
	endpoint: Optional[str] = None,
	start_time: Optional[datetime] = None,
	end_time: Optional[datetime] = None
) -> Dict[str, Any]:
	"""
	Get breakdown of usage by status with success/error rates.
	
	Args:
		db: Database session
		identifier: Optional identifier filter
		api_key: Optional API key filter
		endpoint: Optional endpoint filter
		start_time: Start of time range
		end_time: End of time range
	
	Returns:
		Dict with status breakdown and rates
	"""
	query = db.query(
		UsageLog.status,
		func.count(UsageLog.id).label('count')
	)
	
	if identifier:
		query = query.filter(UsageLog.identifier == identifier)
	if api_key:
		query = query.filter(UsageLog.api_key == api_key)
	if endpoint:
		query = query.filter(UsageLog.endpoint == endpoint)
	if start_time:
		query = query.filter(UsageLog.timestamp >= start_time)
	if end_time:
		query = query.filter(UsageLog.timestamp <= end_time)
	
	query = query.group_by(UsageLog.status)
	results = query.all()
	
	total = sum(r.count for r in results)
	success_count = sum(r.count for r in results if r.status == 'success')
	error_count = total - success_count
	
	breakdown = {r.status: r.count for r in results}
	
	success_rate = (success_count / total * 100) if total > 0 else 0
	error_rate = (error_count / total * 100) if total > 0 else 0
	
	logger.info(f"Status breakdown: {total} total, {success_rate:.1f}% success rate")
	
	return {
		'total_requests': total,
		'success_count': success_count,
		'error_count': error_count,
		'success_rate': round(success_rate, 2),
		'error_rate': round(error_rate, 2),
		'breakdown': breakdown
	}


def get_recent_errors(
	db: Session,
	identifier: Optional[str] = None,
	api_key: Optional[str] = None,
	limit: int = 50,
	hours_back: int = 24
) -> List[UsageLog]:
	"""
	Get recent error logs for debugging.
	
	Args:
		db: Database session
		identifier: Optional identifier filter
		api_key: Optional API key filter
		limit: Maximum number of errors to return
		hours_back: How many hours back to look
	
	Returns:
		List of recent error UsageLog objects
	"""
	cutoff_time = datetime.now(UTC) - timedelta(hours=hours_back)
	
	query = db.query(UsageLog).filter(
		UsageLog.status != 'success',
		UsageLog.timestamp >= cutoff_time
	)
	
	if identifier:
		query = query.filter(UsageLog.identifier == identifier)
	if api_key:
		query = query.filter(UsageLog.api_key == api_key)
	
	query = query.order_by(desc(UsageLog.timestamp)).limit(limit)
	
	errors = query.all()
	
	logger.info(f"Retrieved {len(errors)} recent errors")
	
	return errors


# ============================================================================
# Feature 5: Export & Reporting
# ============================================================================

def export_usage_logs_to_dict(
	db: Session,
	query_params: Optional[UsageLogQuery] = None,
	start_time: Optional[datetime] = None,
	end_time: Optional[datetime] = None,
	limit: Optional[int] = None
) -> List[Dict[str, Any]]:
	"""
	Export usage logs as list of dicts for CSV/JSON export.
	
	Args:
		db: Database session
		query_params: Optional query filters
		start_time: Start of time range
		end_time: End of time range
		limit: Maximum number of records
	
	Returns:
		List of usage log dicts
	"""
	logs = get_usage_events(db, query_params)
	
	# Apply additional filters
	if start_time:
		logs = [log for log in logs if log.timestamp >= start_time]
	if end_time:
		logs = [log for log in logs if log.timestamp <= end_time]
	
	# Apply limit
	if limit:
		logs = logs[:limit]
	
	export_data = [
		{
			'id': log.id,
			'api_key': log.api_key,
			'customer_id': log.customer_id,
			'endpoint': log.endpoint,
			'identifier': log.identifier,
			'timestamp': log.timestamp.isoformat() if log.timestamp else None,
			'status': log.status
		}
		for log in logs
	]
	
	logger.info(f"Exported {len(export_data)} usage logs")
	
	return export_data


def generate_usage_report(
	db: Session,
	identifier: Optional[str] = None,
	api_key: Optional[str] = None,
	start_time: Optional[datetime] = None,
	end_time: Optional[datetime] = None
) -> Dict[str, Any]:
	"""
	Generate comprehensive usage report with multiple metrics.
	
	Args:
		db: Database session
		identifier: Optional identifier filter
		api_key: Optional API key filter
		start_time: Start of report period
		end_time: End of report period
	
	Returns:
		Dict containing comprehensive usage report
	"""
	if not end_time:
		end_time = datetime.now(UTC)
	if not start_time:
		start_time = end_time - timedelta(days=30)
	
	# Get basic counts
	query = db.query(UsageLog).filter(
		UsageLog.timestamp >= start_time,
		UsageLog.timestamp <= end_time
	)
	
	if identifier:
		query = query.filter(UsageLog.identifier == identifier)
	if api_key:
		query = query.filter(UsageLog.api_key == api_key)
	
	total_requests = query.count()
	
	# Get status breakdown
	status_breakdown = get_status_breakdown(
		db, identifier, api_key, None, start_time, end_time
	)
	
	# Get endpoint summary
	endpoint_summary = summarize_usage(db, 'endpoint', api_key, identifier)
	
	# Get time series
	time_series = get_usage_time_series(
		db, identifier, api_key, None, start_time, end_time, 'day'
	)
	
	# Calculate averages
	days_in_period = (end_time - start_time).days or 1
	avg_daily_requests = total_requests / days_in_period
	
	report = {
		'report_period': {
			'start': start_time.isoformat(),
			'end': end_time.isoformat(),
			'days': days_in_period
		},
		'summary': {
			'total_requests': total_requests,
			'avg_daily_requests': round(avg_daily_requests, 2),
			'unique_endpoints': len(endpoint_summary)
		},
		'status_breakdown': status_breakdown,
		'top_endpoints': sorted(endpoint_summary, key=lambda x: x['count'], reverse=True)[:10],
		'time_series': time_series,
		'generated_at': datetime.now(UTC).isoformat()
	}
	
	logger.info(f"Generated usage report: {total_requests} requests over {days_in_period} days")
	
	return report
