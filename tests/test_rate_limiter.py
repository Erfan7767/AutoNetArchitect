"""Tests for API rate limiting."""
from __future__ import annotations

from api.middleware.rate_limiter import RateLimitExceeded, RateLimiter


def test_rate_limiter_blocks_after_limit_and_resets_after_window():
    limiter = RateLimiter(limit=2, window_seconds=10)
    first = limiter.check("client", now=100.0)
    second = limiter.check("client", now=101.0)
    assert first.remaining == 1
    assert second.remaining == 0
    blocked = False
    try:
        limiter.check("client", now=102.0)
    except RateLimitExceeded as exc:
        blocked = True
        assert exc.retry_after >= 1
    if not blocked:
        raise AssertionError("third request should be rate limited")
    after_window = limiter.check("client", now=111.0)
    assert after_window.request_count == 1


def test_rate_limiter_keeps_keys_isolated():
    limiter = RateLimiter(limit=1, window_seconds=10)
    limiter.check("one", now=100.0)
    second_key = limiter.check("two", now=100.0)
    assert second_key.key == "two"
