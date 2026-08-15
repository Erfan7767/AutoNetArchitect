"""Domain event constructors for system_events."""
from ..event_models import Event
def create_system_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="system_events", payload=payload)
