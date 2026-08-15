"""Concurrency limiter."""
import asyncio
class ConcurrencyLimiter:
    """Limit concurrent operations."""
    def __init__(self, limit: int) -> None: self.semaphore = asyncio.Semaphore(limit)
