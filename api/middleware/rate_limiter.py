"""Thread-safe local rate limiter for the V1 API."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import threading
from typing import Deque

from fastapi import HTTPException, Request, status


class RateLimitExceeded(RuntimeError):
    """Raised when one client exceeds the configured request window."""

    def __init__(self, retry_after: int) -> None:
        """Store the bounded retry interval."""
        super().__init__("rate limit exceeded")
        self.retry_after = max(1, int(retry_after))


@dataclass(frozen=True)
class RateLimitSnapshot:
    """Read-only limiter state for one key."""

    key: str
    limit: int
    window_seconds: int
    request_count: int
    remaining: int
    retry_after: int


class RateLimiter:
    """In-memory fixed-window limiter appropriate for a single API process in V1."""

    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        """Create a limiter with positive bounded settings."""
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, Deque[float]] = {}
        self._lock = threading.RLock()

    def check(self, key: str, *, now: float | None = None) -> RateLimitSnapshot:
        """Consume one request slot or raise RateLimitExceeded."""
        if not key:
            raise ValueError("rate limit key is required")
        current = now if now is not None else datetime.now(timezone.utc).timestamp()
        with self._lock:
            events = self._events.setdefault(key, deque())
            cutoff = current - self.window_seconds
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                retry_after = int(max(1, events[0] + self.window_seconds - current))
                raise RateLimitExceeded(retry_after)
            events.append(current)
            return RateLimitSnapshot(key, self.limit, self.window_seconds, len(events), self.limit - len(events), 0)

    def reset(self, key: str | None = None) -> None:
        """Clear one client key or all local keys."""
        with self._lock:
            if key is None:
                self._events.clear()
            else:
                self._events.pop(key, None)

    async def dependency(self, request: Request) -> None:
        """FastAPI dependency that limits requests by remote host and route scope."""
        api_context = request.app.state.api_context
        host = request.client.host if request.client is not None else "unknown"
        key = f"{host}:{request.url.path.split('/')[1] if len(request.url.path.split('/')) > 1 else 'root'}"
        try:
            snapshot = api_context.rate_limiter.check(key)
        except RateLimitExceeded as exc:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate limit exceeded", headers={"Retry-After": str(exc.retry_after)}) from exc
        request.state.rate_limit = snapshot
