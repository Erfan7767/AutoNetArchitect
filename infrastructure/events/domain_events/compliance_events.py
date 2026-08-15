"""Domain event constructors for compliance_events."""
from ..event_models import Event
def create_compliance_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="compliance_events", payload=payload)
