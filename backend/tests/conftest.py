import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base, get_db
from backend.models.auth import AuthToken
from backend.models.user import User
from backend.models.api_key import APIKey
from backend.models.audit_log import AuditLog
from backend.models.usage_log import UsageLog
from backend.models.rate_limit import RateLimitConfig
from backend.models.stats import UsageStats
from backend.models.settings import UserSettings
# Add other models here if needed
from datetime import datetime, timedelta, UTC


# Use an in-memory SQLite database for testing
@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return engine

# Clean up usage_stats table after each test for isolation
import backend.models.stats
@pytest.fixture(autouse=True)
def cleanup_usage_stats(db_session):
    yield
    db_session.query(backend.models.stats.UsageStats).delete()
    db_session.commit()

@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_user(db_session):
    user = User(id="1", email="test@example.com", hashed_password="hashed", is_active=True)
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="function")
def token_data(test_user):
    return {
        "user_id": int(test_user.id),
        "token": "testtoken",
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
        "is_active": True
    }

@pytest.fixture(scope="function")
def usage_stats(db_session, test_user):
    from backend.models.stats import UsageStats
    stats = UsageStats(user_id=int(test_user.id), endpoint="/endpoint1", count=5, period="day")
    db_session.add(stats)
    db_session.commit()
    return stats

@pytest.fixture(scope="function")
def usage_log(db_session, test_user):
    from backend.models.usage_log import UsageLog
    # Use test_user.id as identifier so summarize_usage with identifier=user_id will match
    log = UsageLog(id="log1", api_key="key1", customer_id=test_user.id, endpoint="/endpoint1", identifier=str(test_user.id), timestamp=datetime.now(UTC), status="allowed")
    db_session.add(log)
    db_session.commit()
    return log
