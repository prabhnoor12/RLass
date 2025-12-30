from sqlalchemy.orm import Session
from ..crud import audit_log as crud_audit_log
from ..schemas.audit_log import AuditLogQuery
from ..models.audit_log import AuditLog
from typing import List, Optional

def log_audit_event(
		db: Session,
		action: str,
		actor_id: str,
		target: Optional[str] = None,
		details: Optional[str] = None,
		event_type: Optional[str] = None,
		ip_address: Optional[str] = None,
		user_agent: Optional[str] = None
	) -> AuditLog:
		"""
		Log an audit event to the database, with security insights.
		"""
		return crud_audit_log.log_action(
			db,
			action,
			actor_id,
			target,
			details,
			event_type,
			ip_address,
			user_agent
		)


def get_audit_events(
	db: Session,
	query: Optional[AuditLogQuery] = None,
	limit: Optional[int] = None,
	offset: Optional[int] = None
) -> List[AuditLog]:
	"""
	Retrieve audit logs, optionally filtered and paginated.
	"""
	q = db.query(AuditLog)
	if query:
		if query.actor_id:
			q = q.filter(AuditLog.actor_id == query.actor_id)
		if query.action:
			q = q.filter(AuditLog.action == query.action)
		if query.target:
			q = q.filter(AuditLog.target == query.target)
		if query.from_time:
			q = q.filter(AuditLog.timestamp >= query.from_time)
		if query.to_time:
			q = q.filter(AuditLog.timestamp <= query.to_time)
	q = q.order_by(AuditLog.timestamp.desc())
	if offset:
		q = q.offset(offset)
	if limit:
		q = q.limit(limit)
	return q.all()

def summarize_audit_events_by_actor(db: Session, from_time: Optional[str] = None, to_time: Optional[str] = None) -> dict:
	"""
	Summarize audit events by actor (user), returning a count per actor.
	"""
	from sqlalchemy import func
	q = db.query(AuditLog.actor_id, func.count(AuditLog.id)).group_by(AuditLog.actor_id)
	if from_time:
		q = q.filter(AuditLog.timestamp >= from_time)
	if to_time:
		q = q.filter(AuditLog.timestamp <= to_time)
	return dict(q.all())

def summarize_audit_events_by_action(db: Session, from_time: Optional[str] = None, to_time: Optional[str] = None) -> dict:
	"""
	Summarize audit events by action type, returning a count per action.
	"""
	from sqlalchemy import func
	q = db.query(AuditLog.action, func.count(AuditLog.id)).group_by(AuditLog.action)
	if from_time:
		q = q.filter(AuditLog.timestamp >= from_time)
	if to_time:
		q = q.filter(AuditLog.timestamp <= to_time)
	return dict(q.all())
