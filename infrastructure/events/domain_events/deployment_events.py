"""Domain event constructors for deployment_events."""
from ..event_models import Event
def create_deployment_events(payload: dict[str, object]) -> Event:
    """Create a typed domain event."""
    return Event(event_type="deployment_events", payload=payload)
