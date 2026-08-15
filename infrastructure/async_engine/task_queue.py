"""Async task queue."""
import asyncio
class TaskQueue:
    """Queue tasks safely."""
    def __init__(self) -> None: self.queue = asyncio.Queue()
    async def put(self, task: object) -> None: """Put a task."""; await self.queue.put(task)
    async def get(self) -> object: """Get a task."""; return await self.queue.get()
