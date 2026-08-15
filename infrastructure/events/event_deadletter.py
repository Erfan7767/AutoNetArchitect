"""Dead-letter event storage."""
class DeadLetterQueue:
    """Retain events that failed delivery."""
    def __init__(self) -> None: self.events = []
    def add(self, event: object, error: str) -> None: """Store a failed event and reason."""; self.events.append((event, error))
