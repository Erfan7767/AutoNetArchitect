"""Task status monitor."""
class TaskMonitor:
    """Track task statuses."""
    def __init__(self) -> None: self.statuses = {}
    def set_status(self, task_id: str, status: str) -> None: """Set a task status."""; self.statuses[task_id] = status
