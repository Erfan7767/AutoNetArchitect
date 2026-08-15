"""Event handler protocol for synchronous infrastructure events."""

from __future__ import annotations

from typing import Protocol

from .event_models import Event


class EventHandler(Protocol):
    """Protocol for synchronous event consumers."""

    def handle(self, event: Event) -> None:
        """Handle one event in a concrete consumer implementation."""
        raise TypeError("EventHandler.handle requires a concrete consumer implementation")
