"""Domain event constructors for security_events."""
from ..event_models import Event
def create_security_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="security_events", payload=payload)
