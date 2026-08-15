"""Domain event constructors for incident_events."""
from ..event_models import Event
def create_incident_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="incident_events", payload=payload)
