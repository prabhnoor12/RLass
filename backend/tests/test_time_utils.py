import pytest
import time
from datetime import datetime
from backend.utils import time_utils

def test_current_unix_timestamp_is_int_and_recent():
    ts = time_utils.current_unix_timestamp()
    assert isinstance(ts, int)
    now = int(time.time())
    # Allow a small delta for timing
    assert abs(now - ts) < 3

def test_format_unix_timestamp_returns_iso8601():
    ts = 1609459200  # 2021-01-01T00:00:00Z
    formatted = time_utils.format_unix_timestamp(ts)
    assert formatted == '2021-01-01T00:00:00Z'

def test_seconds_until_reset_basic():
    period = 60  # 1 minute
    # Simulate just after a window start
    now = int(time.time())
    result = time_utils.seconds_until_reset(period)
    assert 0 <= result <= period
    # Should be close to period if just after window start
    if now % period < 2:
        assert period - 2 <= result <= period
