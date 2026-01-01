import time
import datetime

def current_unix_timestamp() -> int:
    """Return the current Unix timestamp as an integer."""
    return int(time.time())

def format_unix_timestamp(ts: int) -> str:
    """Format a Unix timestamp as an ISO8601 string."""
    return datetime.datetime.fromtimestamp(ts, datetime.UTC).isoformat() + 'Z'

def seconds_until_reset(period_seconds: int) -> int:
    """Return seconds until the next reset window."""
    now = int(time.time())
    window_start = now - (now % period_seconds)
    reset = window_start + period_seconds
    return max(0, reset - now)
