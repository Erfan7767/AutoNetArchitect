"""Task cancellation management."""
class CancellationManager:
    """Track cancellation requests."""
    def __init__(self) -> None: self.cancelled = set()
    def cancel(self, task_id: str) -> None: """Request cancellation."""; self.cancelled.add(task_id)
