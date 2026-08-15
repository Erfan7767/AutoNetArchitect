"""Cache manager with an in-memory backend."""
class CacheManager:
    """Store and retrieve values by key."""
    def __init__(self) -> None: self._values = {}
    def get(self, key: str, default: object = None) -> object: """Get a cached value."""; return self._values.get(key, default)
    def set(self, key: str, value: object) -> None: """Cache a value."""; self._values[key] = value
    def invalidate(self, key: str) -> None: """Remove a cached value."""; self._values.pop(key, None)
