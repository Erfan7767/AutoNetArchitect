"""Async task models."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable
@dataclass
class Task:
    """A scheduled coroutine task."""
    task_id: str
    operation: Callable[[], Awaitable[Any]]
    metadata: dict[str, Any] = field(default_factory=dict)
