"""Domain event constructors for config_events."""
from ..event_models import Event
def create_config_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="config_events", payload=payload)
