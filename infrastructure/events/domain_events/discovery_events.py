"""Domain event constructors for discovery_events."""
from ..event_models import Event
def create_discovery_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="discovery_events", payload=payload)
