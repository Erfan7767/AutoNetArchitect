"""Event middleware chain."""
class EventMiddleware:
    """Apply a transformation before dispatch."""
    def process(self, event: object, next_handler: object) -> object: """Process and forward an event."""; return next_handler(event)
