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
