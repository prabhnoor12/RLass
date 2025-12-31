import pytest
from backend.services import rate_limiter as rl_service
from backend.crud import rate_limit as crud_rate_limit
from backend.schemas.rate_limit import RateLimitConfigCreate
from backend.models.rate_limit import RateLimitConfig

@pytest.fixture
def api_key(test_user, db_session):
    from backend.crud.api_key import create_api_key
    from backend.schemas.api_key import APIKeyCreate
    api_key_obj = create_api_key(db_session, APIKeyCreate(user_id=test_user.id))
    return api_key_obj.key

@pytest.fixture
def rate_limit_config(api_key, db_session):
    config_in = RateLimitConfigCreate(
        api_key=api_key,
        customer_id=None,
        endpoint="/test",
        limit=3,
        period_seconds=60
    )
    return crud_rate_limit.create_rate_limit(db_session, config_in)

def test_create_and_get_rate_limit(db_session, api_key):
    config_in = RateLimitConfigCreate(
        api_key=api_key,
        customer_id=None,
        endpoint="/rl",
        limit=5,
        period_seconds=120
    )
    config = crud_rate_limit.create_rate_limit(db_session, config_in)
    fetched = crud_rate_limit.get_rate_limit(db_session, api_key, endpoint="/rl")
    assert fetched is not None
    assert fetched.limit == 5
    assert fetched.period_seconds == 120

def test_update_and_delete_rate_limit(db_session, api_key):
    config_in = RateLimitConfigCreate(
        api_key=api_key,
        customer_id=None,
        endpoint="/update",
        limit=2,
        period_seconds=30
    )
    crud_rate_limit.create_rate_limit(db_session, config_in)
    updated = crud_rate_limit.update_rate_limit(db_session, api_key, "/update", 10, 300)
    assert updated is not None
    assert updated.limit == 10
    assert updated.period_seconds == 300
    deleted = crud_rate_limit.delete_rate_limit(db_session, api_key, "/update")
    assert deleted is True
    assert crud_rate_limit.get_rate_limit(db_session, api_key, "/update") is None

def test_rate_limiter_check_and_log(db_session, api_key, rate_limit_config):
    allowed, remaining, window_end = rl_service.check_and_log_rate_limit(
        db_session, api_key, identifier="user1", endpoint="/test"
    )
    assert allowed is True
    assert remaining == 2
    # Exceed limit
    rl_service.check_and_log_rate_limit(db_session, api_key, "user1", "/test")
    rl_service.check_and_log_rate_limit(db_session, api_key, "user1", "/test")
    allowed, remaining, _ = rl_service.check_and_log_rate_limit(db_session, api_key, "user1", "/test")
    assert allowed is False
    assert remaining == 0

def test_summarize_and_reset_usage(db_session, api_key, rate_limit_config):
    # Use up the limit
    for _ in range(3):
        rl_service.check_and_log_rate_limit(db_session, api_key, "user2", "/test")
    summary = rl_service.summarize_usage_for_api_key(db_session, api_key, "/test")
    assert summary["total"] == 3
    assert summary["allowed"] == 3
    assert summary["rate_limited"] == 0
    # Exceed limit
    rl_service.check_and_log_rate_limit(db_session, api_key, "user2", "/test")
    summary = rl_service.summarize_usage_for_api_key(db_session, api_key, "/test")
    assert summary["rate_limited"] == 1
    # Reset
    count = rl_service.reset_usage_logs_for_api_key(db_session, api_key, "/test")
    assert count > 0
    summary = rl_service.summarize_usage_for_api_key(db_session, api_key, "/test")
    assert summary["total"] == 0

def test_in_memory_backend_config_and_usage():
    backend = rl_service.InMemoryRateLimitBackend()
    class DummyConfig:
        limit = 2
        period_seconds = 60
    config = DummyConfig()
    api_key = "memkey"
    endpoint = "/mem"
    backend.set_config(api_key, endpoint, config)
    # Should allow twice, then block
    allowed1, remaining1, _ = backend.check_and_log(api_key, "id", endpoint, config, False)
    allowed2, remaining2, _ = backend.check_and_log(api_key, "id", endpoint, config, False)
    allowed3, remaining3, _ = backend.check_and_log(api_key, "id", endpoint, config, False)
    assert allowed1 is True and allowed2 is True and allowed3 is False
    assert remaining3 == 0
    # Reset usage
    backend.reset_usage(api_key, endpoint)
    allowed4, _, _ = backend.check_and_log(api_key, "id", endpoint, config, False)
    assert allowed4 is True

def test_backend_switching_and_unlimited(db_session, api_key):
    rl = rl_service.RateLimiter(db=db_session, use_in_memory=True)
    class DummyConfig:
        limit = 1
        period_seconds = 60
    rl.set_in_memory_config(api_key, "/switch", DummyConfig())
    allowed, remaining, _ = rl.check_and_log_rate_limit(api_key, "id", "/switch")
    assert allowed is True
    allowed, remaining, _ = rl.check_and_log_rate_limit(api_key, "id", "/switch")
    assert allowed is False
    # Switch to DB backend
    rl.set_test_mode(False)
    # No config in DB, should be unlimited
    allowed, remaining, _ = rl.check_and_log_rate_limit(api_key, "id", "/notset")
    assert allowed is True and remaining == -1

def test_get_rate_limit_config(db_session, api_key, rate_limit_config):
    config = rl_service.get_rate_limit_config(db_session, api_key, "/test")
    assert config is not None
    config2 = rl_service.get_rate_limit_config(db_session, api_key, "/notexist")
    assert config2 is None
