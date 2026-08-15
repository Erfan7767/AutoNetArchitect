"""Lifetime scopes for dependency injection."""
from __future__ import annotations
from enum import Enum
from contextlib import contextmanager
from typing import Any, Iterator
import threading

class Scope(str, Enum):
    """Supported service lifetimes."""
    SINGLETON = 'singleton'
    TRANSIENT = 'transient'
    SCOPED = 'scoped'
    THREAD_LOCAL = 'thread_local'

class ScopeManager:
    """Create nested scopes and retain scoped instances."""
    def __init__(self) -> None:
        self._local = threading.local()
    def _stack(self) -> list[dict[object, Any]]:
        if not hasattr(self._local, 'stack'): self._local.stack = []
        return self._local.stack
    @contextmanager
    def create(self) -> Iterator[dict[object, Any]]:
        """Create a scope and clear its instances on exit."""
        scope: dict[object, Any] = {}; self._stack().append(scope)
        try: yield scope
        finally: self._stack().pop()
    def current(self) -> dict[object, Any]:
        """Return the active scope or raise an error."""
        stack = self._stack()
        if not stack: raise RuntimeError('no active scope')
        return stack[-1]
