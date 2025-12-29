from sqlalchemy.orm import Session, joinedload
from ..models.rate_limit import RateLimitConfig
from ..schemas.rate_limit import RateLimitConfigCreate
from typing import Optional, List

def create_rate_limit(db: Session, config_in: RateLimitConfigCreate) -> RateLimitConfig:
    """Create and store a new rate limit configuration in the database."""
    db_config = RateLimitConfig(
        api_key=config_in.api_key,
        endpoint=config_in.endpoint,
        limit=config_in.limit,
        period_seconds=config_in.period_seconds
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def get_rate_limit(db: Session, api_key: str, endpoint: Optional[str] = None) -> Optional[RateLimitConfig]:
    """Retrieve a rate limit configuration by api_key and endpoint from the database."""
    q = db.query(RateLimitConfig).filter(RateLimitConfig.api_key == api_key).options(
        joinedload(RateLimitConfig.api_key_obj)
    )
    if endpoint:
        q = q.filter(RateLimitConfig.endpoint == endpoint)
    else:
        q = q.filter(RateLimitConfig.endpoint.is_(None))
    return q.first()

def update_rate_limit(db: Session, api_key: str, endpoint: Optional[str], limit: int, period_seconds: int) -> Optional[RateLimitConfig]:
    """Update an existing rate limit configuration in the database."""
    q = db.query(RateLimitConfig).filter(RateLimitConfig.api_key == api_key)
    if endpoint:
        q = q.filter(RateLimitConfig.endpoint == endpoint)
    else:
        q = q.filter(RateLimitConfig.endpoint.is_(None))
    config = q.first()
    if config:
        config.limit = limit
        config.period_seconds = period_seconds
        db.commit()
        db.refresh(config)
        return config
    return None

def delete_rate_limit(db: Session, api_key: str, endpoint: Optional[str] = None) -> bool:
    """Delete a rate limit configuration from the database."""
    q = db.query(RateLimitConfig).filter(RateLimitConfig.api_key == api_key)
    if endpoint:
        q = q.filter(RateLimitConfig.endpoint == endpoint)
    else:
        q = q.filter(RateLimitConfig.endpoint.is_(None))
    config = q.first()
    if config:
        db.delete(config)
        db.commit()
        return True
    return False

def list_rate_limits(db: Session, api_key: Optional[str] = None) -> List[RateLimitConfig]:
    """List all rate limit configurations, optionally filtered by api_key, from the database."""
    query = db.query(RateLimitConfig).options(
        joinedload(RateLimitConfig.api_key_obj)
    )
    if api_key:
        query = query.filter(RateLimitConfig.api_key == api_key)
    return query.all()
