"""Domain event constructors for audit_events."""
from ..event_models import Event
def create_audit_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="audit_events", payload=payload)
