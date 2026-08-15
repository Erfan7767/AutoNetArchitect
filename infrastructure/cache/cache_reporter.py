"""Cache reporting."""
class CacheReporter:
    """Report cache size."""
    def report(self, cache: object) -> dict[str, int]: """Return cache metrics."""; return {"entries": len(getattr(cache, "_values", {}))}
