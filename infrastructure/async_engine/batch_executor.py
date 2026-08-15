"""Batch task executor."""
class BatchExecutor:
    """Execute a batch through an async manager."""
    async def execute(self, manager: object, operations: list[object]) -> object: """Execute a batch."""; return await manager.gather(operations)
