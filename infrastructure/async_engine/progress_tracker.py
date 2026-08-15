"""Progress tracking."""
class ProgressTracker:
    """Track completed work."""
    def __init__(self) -> None: self.completed = 0
    def advance(self, amount: int = 1) -> int: """Advance and return progress."""; self.completed += amount; return self.completed
