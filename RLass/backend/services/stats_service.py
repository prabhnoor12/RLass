
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, UTC
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


# ============================================================================
# Feature 1: Batch Operations
# ============================================================================

def batch_increment_usage(
	db: Session,
	increments: List[Dict[str, Any]]
) -> List[UsageStats]:
	"""
	Efficiently handle multiple stats updates in a single transaction.
	
	Args:
		db: Database session
		increments: List of dicts with 'user_id', 'endpoint', 'period', and optional 'amount'
	
	Returns:
		List of updated/created UsageStats objects
	
	Example:
		increments = [
			{'user_id': 1, 'endpoint': '/api/v1/users', 'period': 'day', 'amount': 5},
			{'user_id': 1, 'endpoint': '/api/v1/posts', 'period': 'day', 'amount': 3},
		]
	"""
	results = []
	
	try:
		for inc in increments:
			user_id = inc['user_id']
			endpoint = inc['endpoint']
			period = inc['period']
			amount = inc.get('amount', 1)
			
			stats = crud_stats.get_usage_stats(db, user_id, endpoint, period)
			if stats:
				stats.count += amount
			else:
				stats = UsageStats(
					user_id=user_id,
					endpoint=endpoint,
					period=period,
					count=amount
				)
				db.add(stats)
			
			results.append(stats)
		
		db.commit()
		
		# Refresh all objects
		for stats in results:
			db.refresh(stats)
		
		logger.info(f"Batch incremented {len(results)} usage stats")
		return results
		
	except Exception as e:
		db.rollback()
		logger.error(f"Batch increment failed: {e}")
		raise


def bulk_create_stats(
	db: Session,
	stats_list: List[UsageStatsCreate]
) -> List[UsageStats]:
	"""
	Create multiple stats entries in a single transaction.
	Skips entries that already exist.
	
	Args:
		db: Database session
		stats_list: List of UsageStatsCreate objects
	
	Returns:
		List of created UsageStats objects
	"""
	created = []
	
	try:
		for stats_in in stats_list:
			existing = crud_stats.get_usage_stats(
				db, 
				stats_in.user_id, 
				stats_in.endpoint, 
				stats_in.period
			)
			
			if not existing:
				db_stats = UsageStats(**stats_in.model_dump())
				db.add(db_stats)
				created.append(db_stats)
			else:
				logger.debug(f"Skipping existing stats: user={stats_in.user_id}, endpoint={stats_in.endpoint}")
		
		db.commit()
		
		for stats in created:
			db.refresh(stats)
		
		logger.info(f"Bulk created {len(created)} stats entries (skipped {len(stats_list) - len(created)})")
		return created
		
	except Exception as e:
		db.rollback()
		logger.error(f"Bulk create failed: {e}")
		raise


# ============================================================================
# Feature 2: Aggregation & Analytics
# ============================================================================

def get_stats_aggregation(
	db: Session,
	user_id: int,
	group_by: str = "endpoint",
	period_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
	"""
	Compute aggregated statistics across different dimensions.
	
	Args:
		db: Database session
		user_id: User identifier
		group_by: Field to group by - 'endpoint' or 'period'
		period_filter: Optional filter for specific period
	
	Returns:
		List of aggregated stats with group, total_count, avg_count, etc.
	"""
	query = db.query(
		getattr(UsageStats, group_by),
		func.sum(UsageStats.count).label('total_count'),
		func.avg(UsageStats.count).label('avg_count'),
		func.max(UsageStats.count).label('max_count'),
		func.min(UsageStats.count).label('min_count'),
		func.count(UsageStats.id).label('record_count')
	).filter(UsageStats.user_id == user_id)
	
	if period_filter:
		query = query.filter(UsageStats.period == period_filter)
	
	query = query.group_by(getattr(UsageStats, group_by))
	results = query.all()
	
	aggregation = [
		{
			group_by: r[0],
			'total_count': r[1] or 0,
			'avg_count': round(float(r[2] or 0), 2),
			'max_count': r[3] or 0,
			'min_count': r[4] or 0,
			'record_count': r[5]
		}
		for r in results
	]
	
	logger.info(f"Aggregated stats for user {user_id} by {group_by}: {len(aggregation)} groups")
	return aggregation


def get_total_usage_by_period(
	db: Session,
	user_id: int,
	start_period: Optional[str] = None,
	end_period: Optional[str] = None
) -> Dict[str, Any]:
	"""
	Get total usage across all endpoints for specified period range.
	
	Args:
		db: Database session
		user_id: User identifier
		start_period: Starting period (inclusive)
		end_period: Ending period (inclusive)
	
	Returns:
		Dict with total usage and breakdown by period
	"""
	query = db.query(
		UsageStats.period,
		func.sum(UsageStats.count).label('total')
	).filter(UsageStats.user_id == user_id)
	
	if start_period:
		query = query.filter(UsageStats.period >= start_period)
	if end_period:
		query = query.filter(UsageStats.period <= end_period)
	
	query = query.group_by(UsageStats.period).order_by(UsageStats.period)
	results = query.all()
	
	period_breakdown = [{'period': r.period, 'total': r.total} for r in results]
	grand_total = sum(r.total for r in results)
	
	logger.info(f"Total usage for user {user_id}: {grand_total} across {len(results)} periods")
	
	return {
		'user_id': user_id,
		'grand_total': grand_total,
		'period_count': len(results),
		'periods': period_breakdown,
		'start_period': start_period,
		'end_period': end_period
	}


# ============================================================================
# Feature 3: Trend Analysis
# ============================================================================

def get_usage_trends(
	db: Session,
	user_id: int,
	endpoint: Optional[str] = None,
	periods: int = 7,
	period_type: str = "day"
) -> Dict[str, Any]:
	"""
	Calculate usage trends and growth rates over recent periods.
	
	Args:
		db: Database session
		user_id: User identifier
		endpoint: Optional endpoint filter
		periods: Number of recent periods to analyze
		period_type: Type of period - 'day', 'hour', etc.
	
	Returns:
		Dict with trend data, growth rate, and direction
	"""
	query = db.query(UsageStats).filter(
		UsageStats.user_id == user_id,
		UsageStats.period.like(f'%{period_type}%')
	)
	
	if endpoint:
		query = query.filter(UsageStats.endpoint == endpoint)
	
	# Get recent periods ordered by timestamp
	stats = query.order_by(desc(UsageStats.timestamp)).limit(periods).all()
	
	if not stats:
		return {
			'user_id': user_id,
			'endpoint': endpoint,
			'trend': 'no_data',
			'growth_rate': 0,
			'periods_analyzed': 0,
			'data_points': []
		}
	
	# Reverse to get chronological order
	stats.reverse()
	
	data_points = [
		{'period': s.period, 'count': s.count, 'timestamp': s.timestamp.isoformat()}
		for s in stats
	]
	
	# Calculate trend
	counts = [s.count for s in stats]
	
	if len(counts) < 2:
		trend = 'stable'
		growth_rate = 0
	else:
		# Simple linear trend: compare first half vs second half
		mid = len(counts) // 2
		first_half_avg = sum(counts[:mid]) / mid
		second_half_avg = sum(counts[mid:]) / (len(counts) - mid)
		
		if second_half_avg > first_half_avg * 1.1:
			trend = 'increasing'
		elif second_half_avg < first_half_avg * 0.9:
			trend = 'decreasing'
		else:
			trend = 'stable'
		
		# Calculate growth rate
		if first_half_avg > 0:
			growth_rate = ((second_half_avg - first_half_avg) / first_half_avg) * 100
		else:
			growth_rate = 0
	
	avg_usage = sum(counts) / len(counts)
	
	logger.info(f"Usage trend for user {user_id}: {trend} (growth: {growth_rate:.1f}%)")
	
	return {
		'user_id': user_id,
		'endpoint': endpoint,
		'trend': trend,
		'growth_rate': round(growth_rate, 2),
		'average_usage': round(avg_usage, 2),
		'periods_analyzed': len(stats),
		'data_points': data_points,
		'total_usage': sum(counts)
	}


def calculate_growth_rate(
	db: Session,
	user_id: int,
	endpoint: str,
	compare_periods: Tuple[str, str]
) -> Dict[str, Any]:
	"""
	Calculate growth rate between two specific periods.
	
	Args:
		db: Database session
		user_id: User identifier
		endpoint: Endpoint to analyze
		compare_periods: Tuple of (earlier_period, later_period)
	
	Returns:
		Dict with growth rate and comparison data
	"""
	period1, period2 = compare_periods
	
	stats1 = crud_stats.get_usage_stats(db, user_id, endpoint, period1)
	stats2 = crud_stats.get_usage_stats(db, user_id, endpoint, period2)
	
	count1 = stats1.count if stats1 else 0
	count2 = stats2.count if stats2 else 0
	
	if count1 > 0:
		growth_rate = ((count2 - count1) / count1) * 100
	else:
		growth_rate = float('inf') if count2 > 0 else 0
	
	absolute_change = count2 - count1
	
	logger.info(f"Growth rate for user {user_id}, endpoint {endpoint}: {growth_rate:.1f}%")
	
	return {
		'user_id': user_id,
		'endpoint': endpoint,
		'period1': period1,
		'period2': period2,
		'count1': count1,
		'count2': count2,
		'absolute_change': absolute_change,
		'growth_rate_percent': round(growth_rate, 2) if growth_rate != float('inf') else 'infinite'
	}


# ============================================================================
# Feature 4: Data Cleanup & Archival
# ============================================================================

def archive_old_stats(
	db: Session,
	days_old: int = 90,
	dry_run: bool = False
) -> Dict[str, Any]:
	"""
	Archive or delete statistics older than specified days.
	
	Args:
		db: Database session
		days_old: Age threshold in days
		dry_run: If True, only count without deleting
	
	Returns:
		Dict with count of archived/deleted records
	"""
	cutoff_date = datetime.now(UTC) - timedelta(days=days_old)
	
	query = db.query(UsageStats).filter(UsageStats.timestamp < cutoff_date)
	count = query.count()
	
	if dry_run:
		logger.info(f"Dry run: Would archive {count} stats older than {days_old} days")
		return {
			'dry_run': True,
			'count': count,
			'cutoff_date': cutoff_date.isoformat(),
			'days_old': days_old
		}
	
	# Actually delete
	deleted = query.delete()
	db.commit()
	
	logger.info(f"Archived {deleted} stats older than {days_old} days")
	
	return {
		'dry_run': False,
		'deleted': deleted,
		'cutoff_date': cutoff_date.isoformat(),
		'days_old': days_old
	}


def delete_stats_by_criteria(
	db: Session,
	user_id: Optional[int] = None,
	endpoint: Optional[str] = None,
	before_date: Optional[datetime] = None,
	period: Optional[str] = None
) -> int:
	"""
	Delete usage stats matching specified criteria.
	
	Args:
		db: Database session
		user_id: Optional user filter
		endpoint: Optional endpoint filter
		before_date: Delete records before this date
		period: Optional period filter
	
	Returns:
		Number of deleted records
	"""
	query = db.query(UsageStats)
	
	if user_id:
		query = query.filter(UsageStats.user_id == user_id)
	if endpoint:
		query = query.filter(UsageStats.endpoint == endpoint)
	if before_date:
		query = query.filter(UsageStats.timestamp < before_date)
	if period:
		query = query.filter(UsageStats.period == period)
	
	count = query.delete()
	db.commit()
	
	logger.info(f"Deleted {count} stats (user={user_id}, endpoint={endpoint}, before={before_date}, period={period})")
	
	return count


def prune_low_value_stats(
	db: Session,
	min_count: int = 1,
	dry_run: bool = False
) -> Dict[str, Any]:
	"""
	Remove stats entries with very low usage counts.
	
	Args:
		db: Database session
		min_count: Minimum count threshold (delete if count <= this)
		dry_run: If True, only count without deleting
	
	Returns:
		Dict with pruning results
	"""
	query = db.query(UsageStats).filter(UsageStats.count <= min_count)
	count = query.count()
	
	if dry_run:
		logger.info(f"Dry run: Would prune {count} stats with count <= {min_count}")
		return {
			'dry_run': True,
			'count': count,
			'min_count': min_count
		}
	
	deleted = query.delete()
	db.commit()
	
	logger.info(f"Pruned {deleted} low-value stats (count <= {min_count})")
	
	return {
		'dry_run': False,
		'deleted': deleted,
		'min_count': min_count
	}


# ============================================================================
# Feature 5: Top/Bottom Rankings
# ============================================================================

def get_top_users_by_usage(
	db: Session,
	period: Optional[str] = None,
	limit: int = 10,
	endpoint: Optional[str] = None
) -> List[Dict[str, Any]]:
	"""
	Get ranking of users by total usage.
	
	Args:
		db: Database session
		period: Optional period filter
		limit: Maximum number of users to return
		endpoint: Optional endpoint filter
	
	Returns:
		List of top users with their usage stats
	"""
	query = db.query(
		UsageStats.user_id,
		func.sum(UsageStats.count).label('total_usage'),
		func.count(UsageStats.id).label('record_count')
	)
	
	if period:
		query = query.filter(UsageStats.period == period)
	if endpoint:
		query = query.filter(UsageStats.endpoint == endpoint)
	
	query = query.group_by(UsageStats.user_id).order_by(desc('total_usage')).limit(limit)
	
	results = query.all()
	
	rankings = [
		{
			'rank': idx + 1,
			'user_id': r.user_id,
			'total_usage': r.total_usage,
			'record_count': r.record_count
		}
		for idx, r in enumerate(results)
	]
	
	logger.info(f"Top {limit} users by usage: {len(rankings)} found")
	
	return rankings


def get_top_endpoints_by_user(
	db: Session,
	user_id: int,
	limit: int = 5,
	period: Optional[str] = None
) -> List[Dict[str, Any]]:
	"""
	Get ranking of endpoints by usage for a specific user.
	
	Args:
		db: Database session
		user_id: User identifier
		limit: Maximum number of endpoints to return
		period: Optional period filter
	
	Returns:
		List of top endpoints with usage data
	"""
	query = db.query(
		UsageStats.endpoint,
		func.sum(UsageStats.count).label('total_usage'),
		func.count(UsageStats.id).label('record_count'),
		func.avg(UsageStats.count).label('avg_usage')
	).filter(UsageStats.user_id == user_id)
	
	if period:
		query = query.filter(UsageStats.period == period)
	
	query = query.group_by(UsageStats.endpoint).order_by(desc('total_usage')).limit(limit)
	
	results = query.all()
	
	rankings = [
		{
			'rank': idx + 1,
			'endpoint': r.endpoint,
			'total_usage': r.total_usage,
			'record_count': r.record_count,
			'avg_usage': round(float(r.avg_usage), 2)
		}
		for idx, r in enumerate(results)
	]
	
	logger.info(f"Top {limit} endpoints for user {user_id}: {len(rankings)} found")
	
	return rankings
