
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from ..crud import api_key as crud_api_key
from ..crud import user as crud_user
from ..schemas.api_key import APIKeyCreate
from ..models.api_key import APIKey
from ..models.user import User
from ..models.usage_log import UsageLog
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, UTC
import logging
import secrets
import hashlib

logger = logging.getLogger("api_key_manager")

def issue_api_key_for_user(db: Session, user_id: str) -> APIKey:
	"""
	Issue a new API key for a given user. Raises ValueError if user not found.
	"""
	user = crud_user.get_user(db, user_id)
	if not user:
		logger.error(f"User not found: {user_id}")
		raise ValueError("User not found")
	api_key_in = APIKeyCreate(user_id=user_id)
	api_key = crud_api_key.create_api_key(db, api_key_in)
	logger.info(f"Issued new API key for user {user_id}")
	# Audit log for key issuance
	from ..services.audit import log_audit_event
	log_audit_event(db, action="issue_api_key", actor_id=user_id, target=api_key.key, event_type="key_usage")
	return api_key

def revoke_api_key(db: Session, key: str) -> bool:
	"""
	Revoke (deactivate) an API key. Returns True if successful.
	"""
	result = crud_api_key.revoke_api_key(db, key)
	if result:
		logger.info(f"Revoked API key: {key}")
		# Audit log for key revocation
		from ..services.audit import log_audit_event
		api_key = crud_api_key.get_api_key(db, key)
		actor_id = api_key.user_id if api_key else None
		log_audit_event(db, action="revoke_api_key", actor_id=actor_id, target=key, event_type="key_usage")
	else:
		logger.warning(f"API key not found for revocation: {key}")
	return result

def list_user_api_keys(db: Session, user_id: str) -> List[APIKey]:
	"""
	List all API keys for a given user.
	"""
	keys = crud_api_key.list_api_keys(db, user_id=user_id)
	logger.info(f"Listed {len(keys)} API keys for user {user_id}")
	return keys

def get_api_key_details(db: Session, key: str) -> Optional[APIKey]:
	"""
	Get details for a specific API key, including user and related info.
	"""
	api_key = crud_api_key.get_api_key(db, key)
	if api_key:
		logger.info(f"Fetched API key details for {key}")
	else:
		logger.warning(f"API key not found: {key}")
	return api_key

def validate_api_key(db: Session, key: str, user_id: Optional[str] = None) -> bool:
	"""
	Validate that an API key exists, is active, and (optionally) belongs to a given user.
	"""
	api_key = crud_api_key.get_api_key(db, key)
	if not api_key or not api_key.is_active:
		logger.warning(f"API key invalid or inactive: {key}")
		return False
	if user_id and api_key.user_id != user_id:
		logger.warning(f"API key {key} does not belong to user {user_id}")
		return False
	logger.info(f"API key {key} validated for user {user_id}")
	return True

def update_api_key_last_used(db: Session, key: str) -> None:
	"""
	Update the last_used timestamp for an API key.
	"""
	crud_api_key.update_last_used(db, key)
	logger.info(f"Updated last_used for API key {key}")
	# Audit log for key usage
	from ..services.audit import log_audit_event
	api_key = crud_api_key.get_api_key(db, key)
	actor_id = api_key.user_id if api_key else None
	log_audit_event(db, action="use_api_key", actor_id=actor_id, target=key, event_type="key_usage")

def reactivate_api_key(db: Session, key: str) -> bool:
	"""
	Reactivate a previously deactivated API key. Returns True if successful.
	"""
	api_key = crud_api_key.get_api_key(db, key)
	if api_key and not api_key.is_active:
		api_key.is_active = True
		db.commit()
		logger.info(f"Reactivated API key {key}")
		return True
	logger.warning(f"API key {key} not found or already active")
	return False

def count_api_keys(db: Session, user_id: Optional[str] = None, active_only: bool = False) -> int:
	"""
	Count API keys, optionally filtered by user and active status.
	"""
	q = db.query(APIKey)
	if user_id:
		q = q.filte


# ============================================================================
# Feature 1: API Key Rotation & Auto-Expiry
# ============================================================================

def rotate_api_key(
	db: Session,
	old_key: str,
	revoke_old: bool = True
) -> Dict[str, Any]:
	"""
	Rotate an API key by creating a new one and optionally revoking the old one.
	This is a critical security feature for key rotation policies.
	
	Args:
		db: Database session
		old_key: The existing API key to rotate
		revoke_old: Whether to revoke the old key (default: True)
	
	Returns:
		Dict with 'new_key', 'old_key', 'old_key_revoked' status
	
	Example:
		result = rotate_api_key(db, "old-key-123", revoke_old=True)
		# Returns: {'new_key': APIKey(...), 'old_key': 'old-key-123', 'old_key_revoked': True}
	"""
	# Get the old key details
	old_api_key = crud_api_key.get_api_key(db, old_key)
	if not old_api_key:
		logger.error(f"API key not found for rotation: {old_key}")
		raise ValueError("API key not found")
	
	user_id = old_api_key.user_id
	
	# Create new key
	new_api_key = issue_api_key_for_user(db, user_id)
	
	# Optionally revoke old key
	old_key_revoked = False
	if revoke_old:
		old_key_revoked = revoke_api_key(db, old_key)
	
	logger.info(f"Rotated API key for user {user_id}: {old_key} -> {new_api_key.key}")
	
	# Audit log for key rotation
	from ..services.audit import log_audit_event
	log_audit_event(
		db, 
		action="rotate_api_key", 
		actor_id=user_id, 
		target=f"old:{old_key},new:{new_api_key.key}", 
		event_type="key_usage"
	)
	
	return {
		'new_key': new_api_key,
		'old_key': old_key,
		'old_key_revoked': old_key_revoked,
		'user_id': user_id
	}


def check_expired_keys(
	db: Session,
	expiry_days: int = 90,
	auto_revoke: bool = False
) -> List[Dict[str, Any]]:
	"""
	Check for API keys that haven't been used in a specified time period.
	Useful for automatic key expiry policies and security compliance.
	
	Args:
		db: Database session
		expiry_days: Days of inactivity before considering a key expired
		auto_revoke: Whether to automatically revoke expired keys
	
	Returns:
		List of expired key details with user info
	
	Example:
		expired = check_expired_keys(db, expiry_days=90, auto_revoke=True)
		# Automatically revokes keys unused for 90+ days
	"""
	cutoff_date = datetime.now(UTC) - timedelta(days=expiry_days)
	
	# Find keys that haven't been used or were last used before cutoff
	query = db.query(APIKey).filter(
		APIKey.is_active == True,
		or_(
			APIKey.last_used == None,
			APIKey.last_used < cutoff_date
		)
	)
	
	expired_keys = query.all()
	
	results = []
	for key_obj in expired_keys:
		days_inactive = (datetime.now(UTC) - (key_obj.last_used or key_obj.created_at)).days
		
		result = {
			'key': key_obj.key,
			'user_id': key_obj.user_id,
			'created_at': key_obj.created_at.isoformat(),
			'last_used': key_obj.last_used.isoformat() if key_obj.last_used else None,
			'days_inactive': days_inactive,
			'revoked': False
		}
		
		if auto_revoke:
			revoked = revoke_api_key(db, key_obj.key)
			result['revoked'] = revoked
		
		results.append(result)
	
	logger.info(f"Found {len(expired_keys)} expired keys (auto_revoke={auto_revoke})")
	
	return results


def batch_revoke_api_keys(
	db: Session,
	keys: List[str],
	reason: Optional[str] = None
) -> Dict[str, Any]:
	"""
	Revoke multiple API keys in a single operation.
	Useful for security incidents or bulk user management.
	
	Args:
		db: Database session
		keys: List of API keys to revoke
		reason: Optional reason for revocation (logged in audit)
	
	Returns:
		Dict with revocation results and statistics
	
	Example:
		result = batch_revoke_api_keys(db, ["key1", "key2", "key3"], reason="security_breach")
	"""
	revoked_count = 0
	failed_keys = []
	
	for key in keys:
		try:
			if revoke_api_key(db, key):
				revoked_count += 1
				
				# Additional audit logging with reason
				if reason:
					from ..services.audit import log_audit_event
					api_key = crud_api_key.get_api_key(db, key)
					if api_key:
						log_audit_event(
							db,
							action=f"batch_revoke_api_key_{reason}",
							actor_id=api_key.user_id,
							target=key,
							event_type="key_usage"
						)
			else:
				failed_keys.append(key)
		except Exception as e:
			logger.error(f"Failed to revoke key {key}: {e}")
			failed_keys.append(key)
	
	logger.info(f"Batch revoked {revoked_count}/{len(keys)} keys (reason: {reason})")
	
	return {
		'total_keys': len(keys),
		'revoked': revoked_count,
		'failed': len(failed_keys),
		'failed_keys': failed_keys,
		'reason': reason
	}


# ============================================================================
# Feature 2: API Key Analytics & Usage Insights
# ============================================================================

def get_api_key_usage_stats(
	db: Session,
	key: str,
	days_back: int = 30
) -> Dict[str, Any]:
	"""
	Get comprehensive usage statistics for a specific API key.
	Provides insights into key activity, endpoints used, and error rates.
	
	Args:
		db: Database session
		key: API key to analyze
		days_back: Number of days to analyze
	
	Returns:
		Dict with usage statistics including total requests, top endpoints, error rates
	
	Example:
		stats = get_api_key_usage_stats(db, "my-api-key", days_back=30)
		# Returns detailed analytics about the key's usage patterns
	"""
	api_key = crud_api_key.get_api_key(db, key)
	if not api_key:
		raise ValueError("API key not found")
	
	cutoff_date = datetime.now(UTC) - timedelta(days=days_back)
	
	# Get usage logs for this key
	usage_query = db.query(UsageLog).filter(
		UsageLog.api_key == key,
		UsageLog.timestamp >= cutoff_date
	)
	
	total_requests = usage_query.count()
	
	# Status breakdown
	status_breakdown = db.query(
		UsageLog.status,
		func.count(UsageLog.id).label('count')
	).filter(
		UsageLog.api_key == key,
		UsageLog.timestamp >= cutoff_date
	).group_by(UsageLog.status).all()
	
	# Top endpoints
	top_endpoints = db.query(
		UsageLog.endpoint,
		func.count(UsageLog.id).label('count')
	).filter(
		UsageLog.api_key == key,
		UsageLog.timestamp >= cutoff_date
	).group_by(UsageLog.endpoint).order_by(desc('count')).limit(10).all()
	
	# Calculate rates
	success_count = sum(r.count for r in status_breakdown if r.status == 'success')
	error_count = total_requests - success_count
	success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
	
	# Activity timeline
	daily_usage = db.query(
		func.date_trunc('day', UsageLog.timestamp).label('date'),
		func.count(UsageLog.id).label('count')
	).filter(
		UsageLog.api_key == key,
		UsageLog.timestamp >= cutoff_date
	).group_by('date').order_by('date').all()
	
	logger.info(f"Generated usage stats for key {key}: {total_requests} requests over {days_back} days")
	
	return {
		'api_key': key,
		'user_id': api_key.user_id,
		'is_active': api_key.is_active,
		'created_at': api_key.created_at.isoformat(),
		'last_used': api_key.last_used.isoformat() if api_key.last_used else None,
		'analysis_period_days': days_back,
		'total_requests': total_requests,
		'success_count': success_count,
		'error_count': error_count,
		'success_rate': round(success_rate, 2),
		'status_breakdown': {r.status: r.count for r in status_breakdown},
		'top_endpoints': [{'endpoint': r.endpoint, 'count': r.count} for r in top_endpoints],
		'daily_usage': [{'date': str(r.date), 'count': r.count} for r in daily_usage]
	}


def get_user_api_keys_summary(
	db: Session,
	user_id: str
) -> Dict[str, Any]:
	"""
	Get a summary of all API keys for a user with their usage metrics.
	Helpful for user dashboards and account management.
	
	Args:
		db: Database session
		user_id: User identifier
	
	Returns:
		Dict with summary of all user's API keys and their status
	
	Example:
		summary = get_user_api_keys_summary(db, "user123")
		# Returns overview of all keys, active/inactive counts, total usage
	"""
	keys = crud_api_key.list_api_keys(db, user_id=user_id)
	
	active_keys = [k for k in keys if k.is_active]
	inactive_keys = [k for k in keys if not k.is_active]
	
	# Get total usage across all keys
	total_usage = db.query(func.count(UsageLog.id)).filter(
		UsageLog.api_key.in_([k.key for k in keys])
	).scalar() or 0
	
	# Find most recently used key
	most_recent = None
	for key in keys:
		if key.last_used and (most_recent is None or key.last_used > most_recent.last_used):
			most_recent = key
	
	# Keys by age
	keys_info = []
	for key in keys:
		age_days = (datetime.now(UTC) - key.created_at).days
		last_used_days = (datetime.now(UTC) - key.last_used).days if key.last_used else None
		
		keys_info.append({
			'key': key.key,
			'is_active': key.is_active,
			'created_at': key.created_at.isoformat(),
			'last_used': key.last_used.isoformat() if key.last_used else None,
			'age_days': age_days,
			'days_since_last_use': last_used_days
		})
	
	logger.info(f"Generated API key summary for user {user_id}: {len(keys)} total keys")
	
	return {
		'user_id': user_id,
		'total_keys': len(keys),
		'active_keys': len(active_keys),
		'inactive_keys': len(inactive_keys),
		'total_usage_all_keys': total_usage,
		'most_recently_used_key': most_recent.key if most_recent else None,
		'keys': keys_info
	}


def get_least_used_keys(
	db: Session,
	limit: int = 10,
	days_back: int = 30
) -> List[Dict[str, Any]]:
	"""
	Identify API keys with lowest usage to help with cleanup decisions.
	Useful for identifying potentially unused or forgotten keys.
	
	Args:
		db: Database session
		limit: Maximum number of keys to return
		days_back: Time period to analyze
	
	Returns:
		List of least-used keys with usage counts
	
	Example:
		unused = get_least_used_keys(db, limit=10, days_back=30)
		# Returns keys that are barely used and could be candidates for revocation
	"""
	cutoff_date = datetime.now(UTC) - timedelta(days=days_back)
	
	# Get usage counts per key
	key_usage = db.query(
		UsageLog.api_key,
		func.count(UsageLog.id).label('usage_count')
	).filter(
		UsageLog.timestamp >= cutoff_date
	).group_by(UsageLog.api_key).all()
	
	# Create dict of usage counts
	usage_dict = {r.api_key: r.usage_count for r in key_usage}
	
	# Get all active keys
	all_keys = db.query(APIKey).filter(APIKey.is_active == True).all()
	
	# Add usage counts (0 for unused keys)
	keys_with_usage = []
	for key in all_keys:
		usage_count = usage_dict.get(key.key, 0)
		keys_with_usage.append({
			'key': key.key,
			'user_id': key.user_id,
			'usage_count': usage_count,
			'created_at': key.created_at.isoformat(),
			'last_used': key.last_used.isoformat() if key.last_used else None
		})
	
	# Sort by usage count (ascending) and limit
	least_used = sorted(keys_with_usage, key=lambda x: x['usage_count'])[:limit]
	
	logger.info(f"Identified {len(least_used)} least-used API keys")
	
	return least_used


# ============================================================================
# Feature 3: Rate Limit Management Integration
# ============================================================================

def set_api_key_rate_limit(
	db: Session,
	key: str,
	max_requests: int,
	window_seconds: int = 3600
) -> Dict[str, Any]:
	"""
	Set or update rate limit for a specific API key.
	Essential for API quota management and preventing abuse.
	
	Args:
		db: Database session
		key: API key to configure
		max_requests: Maximum number of requests allowed
		window_seconds: Time window in seconds (default: 3600 = 1 hour)
	
	Returns:
		Dict with rate limit configuration
	
	Example:
		limit = set_api_key_rate_limit(db, "my-key", max_requests=1000, window_seconds=3600)
		# Sets limit of 1000 requests per hour for this key
	"""
	from ..models.rate_limit import RateLimitConfig
	from ..crud import rate_limit as crud_rate_limit
	
	api_key = crud_api_key.get_api_key(db, key)
	if not api_key:
		raise ValueError("API key not found")
	
	# Check if rate limit already exists for this key
	existing_limit = db.query(RateLimitConfig).filter(
		RateLimitConfig.api_key == key
	).first()
	
	if existing_limit:
		# Update existing
		existing_limit.max_requests = max_requests
		existing_limit.window_seconds = window_seconds
		db.commit()
		db.refresh(existing_limit)
		limit_config = existing_limit
		logger.info(f"Updated rate limit for key {key}: {max_requests}/{window_seconds}s")
	else:
		# Create new rate limit
		from ..schemas.rate_limit import RateLimitCreate
		limit_in = RateLimitCreate(
			api_key=key,
			user_id=api_key.user_id,
			max_requests=max_requests,
			window_seconds=window_seconds
		)
		limit_config = crud_rate_limit.create_rate_limit(db, limit_in)
		logger.info(f"Created rate limit for key {key}: {max_requests}/{window_seconds}s")
	
	# Audit log
	from ..services.audit import log_audit_event
	log_audit_event(
		db,
		action="set_rate_limit",
		actor_id=api_key.user_id,
		target=f"{key}:{max_requests}/{window_seconds}s",
		event_type="key_usage"
	)
	
	return {
		'api_key': key,
		'max_requests': max_requests,
		'window_seconds': window_seconds,
		'rate_limit_id': limit_config.id
	}


def get_api_key_quota_status(
	db: Session,
	key: str,
	window_seconds: Optional[int] = None
) -> Dict[str, Any]:
	"""
	Check current quota usage for an API key against its rate limit.
	Shows how close the key is to hitting its limits.
	
	Args:
		db: Database session
		key: API key to check
		window_seconds: Custom window (uses key's configured window if None)
	
	Returns:
		Dict with quota usage and remaining capacity
	
	Example:
		quota = get_api_key_quota_status(db, "my-key")
		# Returns: {'used': 750, 'limit': 1000, 'remaining': 250, 'percentage': 75.0}
	"""
	from ..models.rate_limit import RateLimitConfig
	
	api_key = crud_api_key.get_api_key(db, key)
	if not api_key:
		raise ValueError("API key not found")
	
	# Get rate limit config
	rate_limit = db.query(RateLimitConfig).filter(
		RateLimitConfig.api_key == key
	).first()
	
	if not rate_limit:
		return {
			'api_key': key,
			'has_rate_limit': False,
			'message': 'No rate limit configured for this key'
		}
	
	# Use configured window or custom
	window = window_seconds or rate_limit.window_seconds
	cutoff_time = datetime.now(UTC) - timedelta(seconds=window)
	
	# Count recent usage
	usage_count = db.query(func.count(UsageLog.id)).filter(
		UsageLog.api_key == key,
		UsageLog.timestamp >= cutoff_time
	).scalar() or 0
	
	remaining = max(0, rate_limit.max_requests - usage_count)
	percentage = (usage_count / rate_limit.max_requests * 100) if rate_limit.max_requests > 0 else 0
	
	status = "ok"
	if percentage >= 90:
		status = "critical"
	elif percentage >= 75:
		status = "warning"
	
	logger.info(f"Quota status for key {key}: {usage_count}/{rate_limit.max_requests} ({percentage:.1f}%)")
	
	return {
		'api_key': key,
		'has_rate_limit': True,
		'used': usage_count,
		'limit': rate_limit.max_requests,
		'remaining': remaining,
		'percentage': round(percentage, 2),
		'window_seconds': window,
		'status': status,
		'window_start': cutoff_time.isoformat()
	}


# ============================================================================
# Feature 4: Secure Key Generation & Validation
# ============================================================================

def generate_secure_api_key(
	prefix: str = "sk",
	length: int = 32
) -> str:
	"""
	Generate a cryptographically secure API key with custom prefix.
	Uses secrets module for secure random generation.
	
	Args:
		prefix: Prefix for the key (e.g., 'sk' for secret key, 'pk' for public key)
		length: Length of random portion (default: 32 characters)
	
	Returns:
		Secure API key string
	
	Example:
		key = generate_secure_api_key(prefix="sk_prod", length=40)
		# Returns: "sk_prod_a3f8d9e2b1c4..."
	"""
	# Generate cryptographically secure random string
	random_bytes = secrets.token_urlsafe(length)
	secure_key = f"{prefix}_{random_bytes}"
	
	logger.debug(f"Generated secure API key with prefix '{prefix}'")
	
	return secure_key


def validate_api_key_format(key: str) -> Dict[str, Any]:
	"""
	Validate the format and structure of an API key.
	Checks for proper length, allowed characters, and structure.
	
	Args:
		key: API key to validate
	
	Returns:
		Dict with validation result and details
	
	Example:
		result = validate_api_key_format("sk_prod_abc123...")
		# Returns: {'valid': True, 'prefix': 'sk_prod', 'length': 45, 'issues': []}
	"""
	issues = []
	
	# Check minimum length
	if len(key) < 20:
		issues.append("Key too short (minimum 20 characters)")
	
	# Check for spaces or invalid characters
	if ' ' in key:
		issues.append("Key contains spaces")
	
	# Try to extract prefix
	prefix = None
	if '_' in key:
		parts = key.split('_', 1)
		prefix = parts[0]
	
	# Check for common patterns
	if key.lower() == key or key.upper() == key:
		issues.append("Key should contain mixed case for better security")
	
	is_valid = len(issues) == 0
	
	return {
		'valid': is_valid,
		'key_length': len(key),
		'prefix': prefix,
		'issues': issues,
		'recommendation': 'Use generate_secure_api_key() for production keys' if not is_valid else 'Key format acceptable'
	}


def hash_api_key(key: str) -> str:
	"""
	Create a hash of an API key for secure storage/comparison.
	Useful for storing key fingerprints without exposing the actual key.
	
	Args:
		key: API key to hash
	
	Returns:
		SHA256 hash of the key
	
	Example:
		key_hash = hash_api_key("my-secret-key")
		# Returns: "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
	"""
	return hashlib.sha256(key.encode()).hexdigest()


# ============================================================================
# Feature 5: Bulk Operations & Key Management
# ============================================================================

def bulk_issue_api_keys(
	db: Session,
	user_ids: List[str],
	keys_per_user: int = 1
) -> Dict[str, Any]:
	"""
	Issue API keys for multiple users at once.
	Useful for onboarding, migrations, or bulk user setup.
	
	Args:
		db: Database session
		user_ids: List of user IDs to issue keys for
		keys_per_user: Number of keys to issue per user
	
	Returns:
		Dict with results of bulk issuance
	
	Example:
		result = bulk_issue_api_keys(db, ["user1", "user2", "user3"], keys_per_user=2)
		# Issues 2 keys for each of the 3 users (6 total keys)
	"""
	issued_keys = []
	failed_users = []
	
	for user_id in user_ids:
		try:
			for _ in range(keys_per_user):
				api_key = issue_api_key_for_user(db, user_id)
				issued_keys.append({
					'user_id': user_id,
					'key': api_key.key,
					'created_at': api_key.created_at.isoformat()
				})
		except Exception as e:
			logger.error(f"Failed to issue keys for user {user_id}: {e}")
			failed_users.append({'user_id': user_id, 'error': str(e)})
	
	logger.info(f"Bulk issued {len(issued_keys)} API keys for {len(user_ids)} users")
	
	return {
		'total_users': len(user_ids),
		'keys_per_user': keys_per_user,
		'total_keys_issued': len(issued_keys),
		'successful_users': len(user_ids) - len(failed_users),
		'failed_users': len(failed_users),
		'issued_keys': issued_keys,
		'failures': failed_users
	}


def cleanup_inactive_keys(
	db: Session,
	inactive_days: int = 180,
	dry_run: bool = True
) -> Dict[str, Any]:
	"""
	Clean up API keys that have been inactive for a specified period.
	Important for security hygiene and compliance with data retention policies.
	
	Args:
		db: Database session
		inactive_days: Days of inactivity before cleanup
		dry_run: If True, only report what would be cleaned (don't actually revoke)
	
	Returns:
		Dict with cleanup results
	
	Example:
		# Test run to see what would be cleaned
		result = cleanup_inactive_keys(db, inactive_days=180, dry_run=True)
		
		# Actually perform cleanup
		result = cleanup_inactive_keys(db, inactive_days=180, dry_run=False)
	"""
	cutoff_date = datetime.now(UTC) - timedelta(days=inactive_days)
	
	# Find inactive keys
	query = db.query(APIKey).filter(
		APIKey.is_active == True,
		or_(
			APIKey.last_used == None,
			APIKey.last_used < cutoff_date
		)
	)
	
	inactive_keys = query.all()
	
	cleaned_keys = []
	for key_obj in inactive_keys:
		days_inactive = (datetime.now(UTC) - (key_obj.last_used or key_obj.created_at)).days
		
		key_info = {
			'key': key_obj.key,
			'user_id': key_obj.user_id,
			'days_inactive': days_inactive,
			'last_used': key_obj.last_used.isoformat() if key_obj.last_used else 'never',
			'revoked': False
		}
		
		if not dry_run:
			revoked = revoke_api_key(db, key_obj.key)
			key_info['revoked'] = revoked
		
		cleaned_keys.append(key_info)
	
	action = "Would clean" if dry_run else "Cleaned"
	logger.info(f"{action} {len(cleaned_keys)} inactive keys (inactive_days={inactive_days})")
	
	return {
		'dry_run': dry_run,
		'inactive_days_threshold': inactive_days,
		'total_inactive_keys': len(cleaned_keys),
		'keys_revoked': sum(1 for k in cleaned_keys if k['revoked']),
		'keys': cleaned_keys
	}


def export_api_keys_report(
	db: Session,
	user_id: Optional[str] = None,
	include_inactive: bool = True
) -> List[Dict[str, Any]]:
	"""
	Export comprehensive report of API keys for auditing or compliance.
	Useful for security audits, compliance reports, or backup purposes.
	
	Args:
		db: Database session
		user_id: Optional filter for specific user
		include_inactive: Whether to include inactive keys
	
	Returns:
		List of API key details for export
	
	Example:
		report = export_api_keys_report(db, include_inactive=True)
		# Returns complete list of all keys with metadata for audit trail
	"""
	query = db.query(APIKey)
	
	if user_id:
		query = query.filter(APIKey.user_id == user_id)
	
	if not include_inactive:
		query = query.filter(APIKey.is_active == True)
	
	keys = query.all()
	
	report = []
	for key_obj in keys:
		# Get usage count
		usage_count = db.query(func.count(UsageLog.id)).filter(
			UsageLog.api_key == key_obj.key
		).scalar() or 0
		
		age_days = (datetime.now(UTC) - key_obj.created_at).days
		last_used_days = (datetime.now(UTC) - key_obj.last_used).days if key_obj.last_used else None
		
		report.append({
			'key': key_obj.key,
			'key_hash': hash_api_key(key_obj.key),
			'user_id': key_obj.user_id,
			'is_active': key_obj.is_active,
			'created_at': key_obj.created_at.isoformat(),
			'last_used': key_obj.last_used.isoformat() if key_obj.last_used else None,
			'age_days': age_days,
			'days_since_last_use': last_used_days,
			'total_usage': usage_count
		})
	
	logger.info(f"Exported API keys report: {len(report)} keys")
	
	return reportr(APIKey.user_id == user_id)
	if active_only:
		q = q.filter(APIKey.is_active == True)
	count = q.count()
	logger.info(f"Counted {count} API keys (user_id={user_id}, active_only={active_only})")
	return count
