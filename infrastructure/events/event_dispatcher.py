"""Event dispatch facade."""
from .event_bus import EventBus
class EventDispatcher:
    """Dispatch through an event bus."""
    def __init__(self, bus: EventBus) -> None: self.bus = bus
    def dispatch(self, event: object) -> int: """Dispatch an event."""; return self.bus.publish(event)
