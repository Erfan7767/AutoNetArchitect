"""Timeout helpers."""
import asyncio
class TimeoutManager:
    """Apply timeouts to awaitables."""
    async def run(self, awaitable: object, seconds: float) -> object: """Wait with a timeout."""; return await asyncio.wait_for(awaitable, seconds)
