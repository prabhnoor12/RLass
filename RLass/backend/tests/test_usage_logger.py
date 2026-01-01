import pytest
from backend.services import usage_logger

def test_log_and_get_usage_event(db_session, test_user):
    api_key = "key1"
    endpoint = "/endpoint1"
    identifier = "id1"
    status = "allowed"
    log = usage_logger.log_usage_event(db_session, api_key, endpoint, identifier, status)
    assert log.api_key == api_key
    logs = usage_logger.get_usage_events(db_session)
    assert any(l.api_key == api_key and l.endpoint == endpoint for l in logs)

def test_count_and_delete_usage_events(db_session, test_user):
    api_key = "key2"
    endpoint = "/endpoint2"
    identifier = "id2"
    status = "allowed"
    # Log two events
    usage_logger.log_usage_event(db_session, api_key, endpoint, identifier, status)
    usage_logger.log_usage_event(db_session, api_key, endpoint, identifier, status)
    count = usage_logger.count_usage_events(db_session, api_key=api_key, endpoint=endpoint, identifier=identifier)
    assert count == 2
    deleted = usage_logger.delete_usage_events(db_session, api_key=api_key, identifier=identifier)
    assert deleted == 2
    count_after = usage_logger.count_usage_events(db_session, api_key=api_key, endpoint=endpoint, identifier=identifier)
    assert count_after == 0

# --- Tests for New Service Features ---

def test_batch_log_usage_events(db_session, test_user):
    events = [
        {'api_key': 'batchkey1', 'endpoint': '/batch1', 'identifier': 'userA', 'status': 'success'},
        {'api_key': 'batchkey2', 'endpoint': '/batch2', 'identifier': 'userA', 'status': 'error'},
    ]
    logs = usage_logger.batch_log_usage_events(db_session, events)
    assert len(logs) == 2
    assert any(l.api_key == 'batchkey1' for l in logs)
    assert any(l.status == 'error' for l in logs)

def test_log_usage_with_retry(db_session, test_user):
    log = usage_logger.log_usage_with_retry(db_session, 'retrykey', '/retry', 'userB', 'success', max_retries=2)
    assert log is not None
    assert log.api_key == 'retrykey'

def test_get_usage_events_filtered(db_session, test_user):
    usage_logger.log_usage_event(db_session, 'filterkey', '/filter', 'userC', 'success')
    result = usage_logger.get_usage_events_filtered(db_session, api_key='filterkey', limit=1)
    assert result['total'] >= 1
    assert len(result['logs']) <= 1

def test_search_usage_logs(db_session, test_user):
    usage_logger.log_usage_event(db_session, 'searchkey', '/search', 'userD', 'success')
    results = usage_logger.search_usage_logs(db_session, 'search')
    assert any(r.api_key == 'searchkey' for r in results)

def test_get_usage_time_series(db_session, test_user):
    usage_logger.log_usage_event(db_session, 'tskey', '/ts', 'userE', 'success')
    series = usage_logger.get_usage_time_series(db_session, identifier='userE', api_key='tskey', interval='day')
    assert isinstance(series, list)

def test_get_hourly_distribution(db_session, test_user):
    usage_logger.log_usage_event(db_session, 'hourkey', '/hour', 'userF', 'success')
    dist = usage_logger.get_hourly_distribution(db_session, identifier='userF', days_back=1)
    assert isinstance(dist, dict)
    assert set(dist.keys()) == set(range(24))

def test_get_status_breakdown(db_session, test_user):
    usage_logger.log_usage_event(db_session, 'statuskey', '/status', 'userG', 'success')
    usage_logger.log_usage_event(db_session, 'statuskey', '/status', 'userG', 'error')
    breakdown = usage_logger.get_status_breakdown(db_session, identifier='userG', api_key='statuskey')
    assert 'success_count' in breakdown and 'error_count' in breakdown

def test_get_recent_errors(db_session, test_user):
    usage_logger.log_usage_event(db_session, 'errorkey', '/err', 'userH', 'error')
    errors = usage_logger.get_recent_errors(db_session, identifier='userH', api_key='errorkey', limit=5)
    assert any(e.status != 'success' for e in errors)

def test_export_usage_logs_to_dict(db_session, test_user):
    usage_logger.log_usage_event(db_session, 'exportkey', '/export', 'userI', 'success')
    export = usage_logger.export_usage_logs_to_dict(db_session)
    assert isinstance(export, list)
    assert any(e['api_key'] == 'exportkey' for e in export)

def test_generate_usage_report(db_session, test_user):
    usage_logger.log_usage_event(db_session, 'reportkey', '/report', 'userJ', 'success')
    report = usage_logger.generate_usage_report(db_session, identifier='userJ', api_key='reportkey')
    assert 'summary' in report and 'status_breakdown' in report
