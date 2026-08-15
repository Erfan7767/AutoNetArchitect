"""Event metrics reporter."""

class EventReporter:
    """Report event counts."""

    def count(self, events: list[object]) -> dict[str, int]:
        """Count events by type."""
        result: dict[str, int] = {}
        for event in events:
            name = getattr(event, "event_type", "unknown")
            result[name] = result.get(name, 0) + 1
        return result
