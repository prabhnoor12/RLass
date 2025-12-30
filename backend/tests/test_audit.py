import pytest
from backend.services import audit
from backend.schemas.audit_log import AuditLogQuery

def test_log_and_get_audit_event(db_session, test_user):
    log = audit.log_audit_event(db_session, action="login", actor_id=test_user.id, target="target1", details="details", event_type="user_action", ip_address="127.0.0.1", user_agent="pytest")
    assert log.action == "login"
    query = AuditLogQuery(actor_id=test_user.id)
    events = audit.get_audit_events(db_session, query)
    assert any(e.action == "login" for e in events)

def test_summarize_audit_events(db_session, test_user):
    # Add two events for actor and one for another
    audit.log_audit_event(db_session, action="update", actor_id=test_user.id)
    audit.log_audit_event(db_session, action="update", actor_id=test_user.id)
    audit.log_audit_event(db_session, action="delete", actor_id="other")
    by_actor = audit.summarize_audit_events_by_actor(db_session)
    assert str(test_user.id) in by_actor.keys()
    by_action = audit.summarize_audit_events_by_action(db_session)
    assert "update" in by_action and by_action["update"] >= 2
