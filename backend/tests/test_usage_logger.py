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
