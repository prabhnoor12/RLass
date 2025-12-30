from sqlalchemy.orm import Session, joinedload
from ..models.rate_limit import RateLimitConfig
from ..schemas.rate_limit import RateLimitConfigCreate
from typing import Optional, List

def create_rate_limit(db: Session, config_in: RateLimitConfigCreate) -> RateLimitConfig:
    """Create and store a new rate limit configuration in the database."""
    # If customer_id is not provided, try to resolve from API key
    customer_id = getattr(config_in, 'customer_id', None)
    if customer_id is None:
        from ..crud.api_key import get_api_key
        api_key_obj = get_api_key(db, config_in.api_key)
        customer_id = getattr(api_key_obj, 'user_id', None)
    db_config = RateLimitConfig(
        api_key=config_in.api_key,
        customer_id=customer_id,
        endpoint=config_in.endpoint,
        limit=config_in.limit,
        period_seconds=config_in.period_seconds
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def get_rate_limit(db: Session, api_key: str, endpoint: Optional[str] = None, customer_id: Optional[str] = None) -> Optional[RateLimitConfig]:
    """Retrieve a rate limit configuration by api_key, endpoint, and optionally customer_id from the database."""
    q = db.query(RateLimitConfig).filter(RateLimitConfig.api_key == api_key).options(
        joinedload(RateLimitConfig.api_key_obj)
    )
    if customer_id:
        q = q.filter(RateLimitConfig.customer_id == customer_id)
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

def list_rate_limits(db: Session, api_key: Optional[str] = None, customer_id: Optional[str] = None) -> List[RateLimitConfig]:
    """List all rate limit configurations, optionally filtered by api_key and customer_id, from the database."""
    query = db.query(RateLimitConfig).options(
        joinedload(RateLimitConfig.api_key_obj)
    )
    if api_key:
        query = query.filter(RateLimitConfig.api_key == api_key)
    if customer_id:
        query = query.filter(RateLimitConfig.customer_id == customer_id)
    return query.all()
