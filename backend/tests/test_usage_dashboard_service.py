import pytest
from backend.services import usage_dashboard_service

def test_get_realtime_usage_stats(db_session, test_user, usage_stats, usage_log):
    result = usage_dashboard_service.get_realtime_usage_stats(db_session, user_id=str(test_user.id))
    assert "usage_summary" in result
    assert "stats" in result
    assert isinstance(result["usage_summary"], list)
    assert isinstance(result["stats"], list)
    # Should contain at least one stat for the test user
    assert any(s["user_id"] == int(test_user.id) for s in result["stats"])
    # Usage summary should have dicts with 'endpoint' and 'count'
    assert any(isinstance(row, dict) and "endpoint" in row and "count" in row for row in result["usage_summary"])
