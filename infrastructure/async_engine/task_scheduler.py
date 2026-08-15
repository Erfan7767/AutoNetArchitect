"""Task scheduler."""
class TaskScheduler:
    """Store scheduled tasks."""
    def __init__(self) -> None: self.tasks = []
    def schedule(self, task: object) -> None: """Schedule a task."""; self.tasks.append(task)
