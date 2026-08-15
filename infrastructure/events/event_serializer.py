"""Event serialization."""
import json
class EventSerializer:
    """Serialize event models to JSON."""
    def dumps(self, event: object) -> str: """Serialize an event."""; return json.dumps(event.model_dump(mode="json"), sort_keys=True)
