"""Event filtering helpers."""
class EventFilter:
    """Filter events by type and source."""
    def matches(self, event: object, event_type: str | None = None, source: str | None = None) -> bool: """Check event predicates."""; return (event_type is None or getattr(event, "event_type", None) == event_type) and (source is None or getattr(event, "source", None) == source)
