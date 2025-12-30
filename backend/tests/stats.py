import pytest
from backend.services import stats_service
from backend.crud import stats as crud_stats
from backend.schemas.stats import UsageStatsCreate
from backend.models.stats import UsageStats
from datetime import datetime, UTC

# --- Fixtures ---

@pytest.fixture
def usage_stats_data(test_user):
    return UsageStatsCreate(
        user_id=int(test_user.id),
        endpoint="/api/test",
        count=0,
        period="day",
        timestamp=datetime.now(UTC)
    )

@pytest.fixture
def created_usage_stats(db_session, usage_stats_data):
    return crud_stats.create_usage_stats(db_session, usage_stats_data)

# --- Tests for CRUD ---

def test_create_usage_stats(db_session, usage_stats_data):
    stats = crud_stats.create_usage_stats(db_session, usage_stats_data)
    assert stats.id is not None
    assert stats.user_id == usage_stats_data.user_id
    assert stats.endpoint == usage_stats_data.endpoint
    assert stats.count == usage_stats_data.count
    assert stats.period == usage_stats_data.period

def test_get_usage_stats(db_session, created_usage_stats, usage_stats_data):
    stats = crud_stats.get_usage_stats(db_session, usage_stats_data.user_id, usage_stats_data.endpoint, usage_stats_data.period)
    assert stats is not None
    assert stats.id == created_usage_stats.id

def test_list_usage_stats(db_session, created_usage_stats, usage_stats_data):
    stats_list = crud_stats.list_usage_stats(db_session, usage_stats_data.user_id)
    assert any(s.id == created_usage_stats.id for s in stats_list)

def test_increment_usage(db_session, usage_stats_data):
    # First increment should create
    stats = crud_stats.increment_usage(db_session, usage_stats_data.user_id, usage_stats_data.endpoint, usage_stats_data.period)
    assert stats.count == 1
    # Second increment should increment
    stats2 = crud_stats.increment_usage(db_session, usage_stats_data.user_id, usage_stats_data.endpoint, usage_stats_data.period)
    assert stats2.count == 2

# --- Tests for Service ---

def test_create_stats_with_check_success(db_session, usage_stats_data):
    stats = stats_service.create_stats_with_check(db_session, usage_stats_data)
    assert stats.id is not None

def test_create_stats_with_check_duplicate(db_session, usage_stats_data):
    stats_service.create_stats_with_check(db_session, usage_stats_data)
    with pytest.raises(ValueError):
        stats_service.create_stats_with_check(db_session, usage_stats_data)

def test_get_stats(db_session, created_usage_stats, usage_stats_data):
    stats = stats_service.get_stats(db_session, usage_stats_data.user_id, usage_stats_data.endpoint, usage_stats_data.period)
    assert stats is not None
    assert stats.id == created_usage_stats.id

def test_list_stats(db_session, created_usage_stats, usage_stats_data):
    stats_list = stats_service.list_stats(db_session, usage_stats_data.user_id)
    assert any(s.id == created_usage_stats.id for s in stats_list)

def test_increment_user_usage(db_session, usage_stats_data):
    stats = stats_service.increment_user_usage(db_session, usage_stats_data.user_id, usage_stats_data.endpoint, usage_stats_data.period)
    assert stats.count == 1
    stats2 = stats_service.increment_user_usage(db_session, usage_stats_data.user_id, usage_stats_data.endpoint, usage_stats_data.period)
    assert stats2.count == 2
