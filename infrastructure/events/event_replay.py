"""Event replay service."""
class EventReplay:
    """Replay events through a callback."""
    def replay(self, events: list[object], callback: object) -> int: """Replay all events."""; [callback(event) for event in events]; return len(events)
