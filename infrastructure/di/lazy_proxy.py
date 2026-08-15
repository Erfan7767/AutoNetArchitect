"""Transparent lazy object proxy."""
from __future__ import annotations
from typing import Callable, Generic, TypeVar
T = TypeVar('T')
class LazyProxy(Generic[T]):
    """Create the wrapped object at first attribute access."""
    def __init__(self, factory: Callable[[], T]) -> None: self._factory = factory; self._instance: T | None = None
    def _get(self) -> T:
        if self._instance is None: self._instance = self._factory()
        return self._instance
    def __getattr__(self, name: str) -> object: return getattr(self._get(), name)
