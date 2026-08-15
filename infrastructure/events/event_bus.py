"""Thread-safe publish-subscribe event bus."""
from __future__ import annotations
from threading import RLock
from typing import Callable
from .event_models import Event
class EventBus:
    """Publish events to handlers by event type."""
    def __init__(self) -> None: self._handlers: dict[str, list[Callable[[Event], None]]] = {}; self._lock = RLock()
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None: """Subscribe a handler."""; self._handlers.setdefault(event_type, []).append(handler)
    def publish(self, event: Event) -> int:
        """Dispatch an event and return handler count."""
        with self._lock: handlers = list(self._handlers.get(event.event_type, []))
        for handler in handlers: handler(event)
        return len(handlers)
