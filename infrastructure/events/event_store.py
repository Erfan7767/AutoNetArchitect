"""In-memory event store."""
class EventStore:
    """Retain published events for replay."""
    def __init__(self) -> None: self.events = []
    def append(self, event: object) -> None: """Append an event."""; self.events.append(event)
    def all(self) -> list[object]: """Return stored events."""; return list(self.events)
