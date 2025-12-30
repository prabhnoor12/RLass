import datetime
from sqlalchemy.orm import Session
from datetime import timedelta
from ..crud import rate_limit as crud_rate_limit
from ..crud import usage_log as crud_usage_log
from ..crud import api_key as crud_api_key
from ..models.usage_log import UsageLog
from ..models.rate_limit import RateLimitConfig
from typing import Optional, Tuple, Any
import threading

# Backend abstraction for rate limit storage
class RateLimitBackend:
    def check_and_log(self, *args, **kwargs):
        raise NotImplementedError
    def summarize_usage(self, *args, **kwargs):
        raise NotImplementedError
    def reset_usage(self, *args, **kwargs):
        raise NotImplementedError
    def get_config(self, *args, **kwargs):
        raise NotImplementedError

# In-memory backend (thread-safe)
class InMemoryRateLimitBackend(RateLimitBackend):
    def __init__(self):
        self.usage = {}
        self.lock = threading.Lock()
        self.configs = {}

    def check_and_log(self, api_key, identifier, endpoint, config, align_to_minute):
        now = datetime.datetime.now(datetime.UTC)
        if align_to_minute:
            window_start = now.replace(second=0, microsecond=0)
        else:
            window_start = now - timedelta(seconds=now.second % config.period_seconds, microseconds=now.microsecond)
        window_start_ts = int(window_start.timestamp())
        window_end_ts = window_start_ts + config.period_seconds
        key = (api_key, identifier, endpoint, window_start_ts)
        with self.lock:
            count = self.usage.get(key, 0)
            allowed = count < config.limit
            if allowed:
                self.usage[key] = count + 1
            remaining = max(0, config.limit - self.usage.get(key, 0))
        return allowed, remaining, window_end_ts

    def summarize_usage(self, api_key, endpoint=None, from_time=None, to_time=None):
        with self.lock:
            total = allowed = rate_limited = 0
            for (k_api_key, _, k_endpoint, _), count in self.usage.items():
                if k_api_key == api_key and (endpoint is None or k_endpoint == endpoint):
                    total += count
                    allowed += count  # In-memory only tracks allowed
            return {"total": total, "allowed": allowed, "rate_limited": rate_limited}

    def reset_usage(self, api_key, endpoint=None):
        with self.lock:
            keys_to_delete = [k for k in self.usage if k[0] == api_key and (endpoint is None or k[2] == endpoint)]
            for k in keys_to_delete:
                del self.usage[k]
            return len(keys_to_delete)

    def get_config(self, api_key, endpoint=None):
        # For test/dev, configs must be set manually
        return self.configs.get((api_key, endpoint))

    def set_config(self, api_key, endpoint, config):
        self.configs[(api_key, endpoint)] = config

# DB backend (existing logic)
class DBRateLimitBackend(RateLimitBackend):
    def __init__(self, db):
        self.db = db
    def check_and_log(self, api_key, identifier, endpoint, config, align_to_minute):
        # Use existing DB logic
        now = datetime.datetime.now(datetime.UTC)
        if align_to_minute:
            window_start = now.replace(second=0, microsecond=0)
        else:
            window_start = now - timedelta(seconds=now.second % config.period_seconds, microseconds=now.microsecond)
        window_start_ts = int(window_start.timestamp())
        window_end_ts = window_start_ts + config.period_seconds
        from ..schemas.usage_log import UsageLogQuery
        usage_query = UsageLogQuery(
            api_key=api_key,
            endpoint=endpoint,
            identifier=identifier,
            from_time=datetime.datetime.fromtimestamp(window_start_ts, datetime.UTC),
            to_time=datetime.datetime.fromtimestamp(window_end_ts, datetime.UTC)
        )
        usage_count = len(crud_usage_log.get_usage_logs(self.db, usage_query))
        if usage_count < config.limit:
            crud_usage_log.log_usage(self.db, api_key, endpoint, identifier, status="allowed")
            allowed = True
        else:
            crud_usage_log.log_usage(self.db, api_key, endpoint, identifier, status="rate_limited")
            allowed = False
        remaining = max(0, config.limit - usage_count - (1 if allowed else 0))
        return allowed, remaining, window_end_ts
    def summarize_usage(self, api_key, endpoint=None, from_time=None, to_time=None):
        from ..schemas.usage_log import UsageLogQuery
        usage_query = UsageLogQuery(
            api_key=api_key,
            endpoint=endpoint,
            from_time=from_time,
            to_time=to_time
        )
        logs = crud_usage_log.get_usage_logs(self.db, usage_query)
        total = len(logs)
        allowed = sum(1 for log in logs if log.status == "allowed")
        rate_limited = sum(1 for log in logs if log.status == "rate_limited")
        return {"total": total, "allowed": allowed, "rate_limited": rate_limited}
    def reset_usage(self, api_key, endpoint=None):
        from ..models.usage_log import UsageLog
        q = self.db.query(UsageLog).filter(UsageLog.api_key == api_key)
        if endpoint:
            q = q.filter(UsageLog.endpoint == endpoint)
        count = q.count()
        q.delete(synchronize_session=False)
        self.db.commit()
        return count
    def get_config(self, api_key, endpoint=None):
        return crud_rate_limit.get_rate_limit(self.db, api_key, endpoint)

# Backend selector/failover
class RateLimiter:
    def __init__(self, db=None, use_in_memory=False, test_mode=False):
        self.db = db
        self.test_mode = test_mode
        self.in_memory_backend = InMemoryRateLimitBackend()
        self.db_backend = DBRateLimitBackend(db) if db else None
        self.active_backend = self.in_memory_backend if (use_in_memory or test_mode or not db) else self.db_backend

    def set_test_mode(self, enabled=True):
        self.test_mode = enabled
        self.active_backend = self.in_memory_backend if enabled else (self.db_backend if self.db else self.in_memory_backend)

    def check_and_log_rate_limit(self, api_key, identifier, endpoint=None, align_to_minute=False):
        config = self.active_backend.get_config(api_key, endpoint)
        if not config and endpoint:
            config = self.active_backend.get_config(api_key, None)
        if not config:
            # No config = unlimited
            return True, -1, -1
        return self.active_backend.check_and_log(api_key, identifier, endpoint, config, align_to_minute)

    def summarize_usage_for_api_key(self, api_key, endpoint=None, from_time=None, to_time=None):
        return self.active_backend.summarize_usage(api_key, endpoint, from_time, to_time)

    def reset_usage_logs_for_api_key(self, api_key, endpoint=None):
        return self.active_backend.reset_usage(api_key, endpoint)

    def set_in_memory_config(self, api_key, endpoint, config):
        self.in_memory_backend.set_config(api_key, endpoint, config)

    def get_rate_limit_config(self, api_key, endpoint=None):
        return self.active_backend.get_config(api_key, endpoint)


def check_and_log_rate_limit(db: Session, api_key: str, identifier: str, endpoint: Optional[str] = None, align_to_minute: bool = False) -> Tuple[bool, int, int]:
    rl = RateLimiter(db=db)
    return rl.check_and_log_rate_limit(api_key, identifier, endpoint, align_to_minute)

def summarize_usage_for_api_key(db: Session, api_key: str, endpoint: Optional[str] = None, from_time: Optional[datetime] = None, to_time: Optional[datetime] = None) -> dict:
    rl = RateLimiter(db=db)
    return rl.summarize_usage_for_api_key(api_key, endpoint, from_time, to_time)

def reset_usage_logs_for_api_key(db: Session, api_key: str, endpoint: Optional[str] = None) -> int:
    rl = RateLimiter(db=db)
    return rl.reset_usage_logs_for_api_key(api_key, endpoint)

def get_rate_limit_config(db: Session, api_key: str, endpoint: Optional[str] = None) -> Optional[RateLimitConfig]:
    rl = RateLimiter(db=db)
    return rl.get_rate_limit_config(api_key, endpoint)
