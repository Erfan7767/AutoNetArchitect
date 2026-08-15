"""Memory cache backend."""
class MemoryBackend:
    """Store values in a dictionary."""
    def __init__(self) -> None: self.values = {}
    def get(self, key: str) -> object: """Get a value."""; return self.values.get(key)
    def set(self, key: str, value: object) -> None: """Set a value."""; self.values[key] = value
