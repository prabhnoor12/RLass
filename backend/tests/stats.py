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


    # --- Tests for New Service Features ---

    def test_batch_increment_usage(db_session, test_user):
        increments = [
            {'user_id': int(test_user.id), 'endpoint': '/api/batch1', 'period': 'day', 'amount': 2},
            {'user_id': int(test_user.id), 'endpoint': '/api/batch2', 'period': 'day', 'amount': 3},
        ]
        results = stats_service.batch_increment_usage(db_session, increments)
        assert len(results) == 2
        assert any(r.endpoint == '/api/batch1' and r.count == 2 for r in results)
        assert any(r.endpoint == '/api/batch2' and r.count == 3 for r in results)

    def test_bulk_create_stats(db_session, test_user):
        from backend.schemas.stats import UsageStatsCreate
        stats_list = [
            UsageStatsCreate(user_id=int(test_user.id), endpoint=f'/api/bulk{i}', count=0, period='day')
            for i in range(2)
        ]
        created = stats_service.bulk_create_stats(db_session, stats_list)
        assert len(created) == 2
        assert all(s.endpoint.startswith('/api/bulk') for s in created)

    def test_get_stats_aggregation(db_session, test_user):
        # Add some stats
        stats_service.increment_user_usage(db_session, int(test_user.id), '/api/agg', 'day')
        stats_service.increment_user_usage(db_session, int(test_user.id), '/api/agg', 'day')
        agg = stats_service.get_stats_aggregation(db_session, int(test_user.id), group_by='endpoint')
        assert any(a['endpoint'] == '/api/agg' and a['total_count'] >= 2 for a in agg)

    def test_get_total_usage_by_period(db_session, test_user):
        stats_service.increment_user_usage(db_session, int(test_user.id), '/api/period', '2025-12-31')
        result = stats_service.get_total_usage_by_period(db_session, int(test_user.id), start_period='2025-12-30', end_period='2025-12-31')
        assert result['grand_total'] >= 1
        assert any(p['period'] == '2025-12-31' for p in result['periods'])

    def test_get_usage_trends(db_session, test_user):
        # Add stats for several periods
        for i in range(3):
            stats_service.increment_user_usage(db_session, int(test_user.id), '/api/trend', f'day{i}')
        trends = stats_service.get_usage_trends(db_session, int(test_user.id), endpoint='/api/trend', periods=3)
        assert trends['periods_analyzed'] == 3
        assert trends['trend'] in ['increasing', 'decreasing', 'stable', 'no_data']

    def test_calculate_growth_rate(db_session, test_user):
        stats_service.increment_user_usage(db_session, int(test_user.id), '/api/growth', '2025-12-30')
        stats_service.increment_user_usage(db_session, int(test_user.id), '/api/growth', '2025-12-31')
        result = stats_service.calculate_growth_rate(db_session, int(test_user.id), '/api/growth', ('2025-12-30', '2025-12-31'))
        assert 'growth_rate_percent' in result

    def test_archive_old_stats(db_session, test_user):
        # Create an old stat
        from backend.models.stats import UsageStats
        import datetime
        old_stat = UsageStats(user_id=int(test_user.id), endpoint='/api/old', count=1, period='old', timestamp=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc))
        db_session.add(old_stat)
        db_session.commit()
        result = stats_service.archive_old_stats(db_session, days_old=365, dry_run=True)
        assert result['count'] >= 1

    def test_delete_stats_by_criteria(db_session, test_user):
        # Create a stat to delete
        stats_service.increment_user_usage(db_session, int(test_user.id), '/api/delete', 'delperiod')
        import datetime
        before_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        deleted = stats_service.delete_stats_by_criteria(db_session, user_id=int(test_user.id), endpoint='/api/delete', before_date=before_date, period='delperiod')
        assert deleted >= 1

    def test_prune_low_value_stats(db_session, test_user):
        # Create a low-value stat
        stats_service.increment_user_usage(db_session, int(test_user.id), '/api/prune', 'pruneperiod')
        result = stats_service.prune_low_value_stats(db_session, min_count=1, dry_run=True)
        assert result['count'] >= 1

    def test_get_top_users_by_usage(db_session, test_user):
        stats_service.increment_user_usage(db_session, int(test_user.id), '/api/topuser', 'day')
        rankings = stats_service.get_top_users_by_usage(db_session, period='day', limit=5)
        assert any(r['user_id'] == int(test_user.id) for r in rankings)

    def test_get_top_endpoints_by_user(db_session, test_user):
        stats_service.increment_user_usage(db_session, int(test_user.id), '/api/topendpoint', 'day')
        rankings = stats_service.get_top_endpoints_by_user(db_session, int(test_user.id), limit=5)
        assert any(r['endpoint'] == '/api/topendpoint' for r in rankings)
