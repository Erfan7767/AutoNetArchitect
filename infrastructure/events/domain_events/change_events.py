"""Domain event constructors for change_events."""
from ..event_models import Event
def create_change_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="change_events", payload=payload)
