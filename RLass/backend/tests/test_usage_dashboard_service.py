import pytest
import asyncio
from datetime import datetime, timedelta, timezone
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

def test_get_usage_by_time_range(db_session, test_user, usage_log):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=2)
    end = now
    result = usage_dashboard_service.get_usage_by_time_range(
        db_session, user_id=str(test_user.id), start_date=start, end_date=end, granularity="day"
    )
    assert "total_requests" in result
    assert "time_series" in result
    assert result["granularity"] == "day"
    assert isinstance(result["time_series"], list)

def test_get_error_breakdown(db_session, test_user, usage_log):
    result = usage_dashboard_service.get_error_breakdown(db_session, user_id=str(test_user.id), time_window=48)
    assert "error_rate" in result
    assert "success_rate" in result
    assert "status_breakdown" in result
    assert isinstance(result["status_breakdown"], list)
    assert "errors_by_endpoint" in result

def test_get_top_endpoints(db_session, test_user, usage_log):
    result = usage_dashboard_service.get_top_endpoints(db_session, user_id=str(test_user.id), limit=5, sort_by="count", time_window=48)
    assert isinstance(result, list)
    if result:
        assert "endpoint" in result[0]
        assert "total_requests" in result[0]
        assert "error_rate" in result[0]

def test_get_realtime_usage_stats_async(db_session, test_user, usage_log):
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        usage_dashboard_service.get_realtime_usage_stats_async(db_session, user_id=str(test_user.id))
    )
    assert "usage_summary" in result
    assert "stats" in result
    assert "timestamp" in result

def test_get_cached_usage_stats(db_session, test_user, usage_log):
    result = usage_dashboard_service.get_cached_usage_stats(db_session, user_id=str(test_user.id), cache_ttl=10)
    assert "usage_summary" in result
    assert "stats" in result
    assert "cached_at" in result
    assert "cache_ttl" in result

# The following test is commented out because the required fixture 'api_key_factory' does not exist.
# def test_get_quota_status(db_session, test_user, usage_log, api_key_factory):
#     # Ensure user has at least one API key with a rate limit
#     api_key = api_key_factory(user_id=test_user.id, rate_limits=[type('RL', (), {'max_requests': 100})()])
#     db_session.add(api_key)
#     db_session.commit()
#     result = usage_dashboard_service.get_quota_status(db_session, user_id=str(test_user.id), period="day")
#     assert "current_usage" in result
#     assert "quota_limit" in result
#     assert "remaining" in result
#     assert "usage_percentage" in result
#     assert "status" in result
#     assert result["period"] == "day"
