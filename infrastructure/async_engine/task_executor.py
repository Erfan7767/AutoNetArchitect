"""Task executor."""
class TaskExecutor:
    """Execute callable tasks."""
    async def execute(self, task: object) -> object: """Execute a task operation."""; return await task.operation()
