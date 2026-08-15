"""Async execution context."""
from contextlib import asynccontextmanager
from typing import AsyncIterator
@asynccontextmanager
async def execution_context() -> AsyncIterator[dict[str, object]]:
    """Provide a managed async execution context."""
    yield {}
