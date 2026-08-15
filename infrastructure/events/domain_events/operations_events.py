"""Domain event constructors for operations_events."""
from ..event_models import Event
def create_operations_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="operations_events", payload=payload)
