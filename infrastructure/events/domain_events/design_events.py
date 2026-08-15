"""Domain event constructors for design_events."""
from ..event_models import Event
def create_design_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="design_events", payload=payload)
