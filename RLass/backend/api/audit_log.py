from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..services.audit import get_audit_events
from ..schemas.audit_log import AuditLogQuery, AuditLogRead
from ..database import get_db
from ..utils.response import success_response
from typing import Optional

router = APIRouter()

@router.get("/logs/export")
def export_audit_logs(
    actor_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    target: Optional[str] = Query(None),
    from_time: Optional[str] = Query(None),
    to_time: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Export audit logs with optional filters.
    """
    query = AuditLogQuery(
        actor_id=actor_id,
        action=action,
        target=target,
        from_time=from_time,
        to_time=to_time
    )
    logs = get_audit_events(db, query)
    # Use Pydantic model for serialization and ensure datetime is JSON serializable
    return success_response([
        AuditLogRead.model_validate(log).model_dump(mode="json") for log in logs
    ])
