"""Cache statistics."""
class CacheStatistics:
    """Track cache operations."""
    def __init__(self) -> None: self.hits = 0; self.misses = 0
    def report(self) -> dict[str, int]: """Return counters."""; return {"hits": self.hits, "misses": self.misses}
