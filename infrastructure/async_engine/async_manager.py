"""Async task manager."""
from __future__ import annotations
import asyncio
from typing import Any, Awaitable, Callable
class AsyncManager:
    """Run coroutine operations with bounded concurrency."""
    async def run(self, operation: Callable[[], Awaitable[Any]]) -> Any: """Await one operation."""; return await operation()
    async def gather(self, operations: list[Callable[[], Awaitable[Any]]]) -> list[Any]: """Run operations concurrently."""; return list(await asyncio.gather(*(op() for op in operations)))
