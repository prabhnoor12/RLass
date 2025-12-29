
from sqlalchemy.orm import Session, joinedload
from ..models.audit_log import AuditLog
from ..schemas.audit_log import AuditLogQuery
from datetime import datetime
from typing import Optional, List
import uuid

def log_action(
    db: Session,
    action: str,
    actor_id: str,
    target: Optional[str] = None,
    details: Optional[str] = None
) -> AuditLog:
    """
    Log an audit action to the database.
    """
    entry = AuditLog(
        id=str(uuid.uuid4()),
        action=action,
        actor_id=actor_id,
        target=target,
        timestamp=datetime.utcnow(),
        details=details
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_audit_logs(db: Session, query: Optional[AuditLogQuery] = None) -> List[AuditLog]:
    """
    Retrieve audit logs from the database, optionally filtered by query parameters.
    """
    q = db.query(AuditLog).options(
        joinedload(AuditLog.actor)
    )
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
    return q.all()
