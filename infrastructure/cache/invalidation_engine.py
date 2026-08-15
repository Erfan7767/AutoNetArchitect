"""Cache invalidation engine."""
class InvalidationEngine:
    """Invalidate keys by prefix."""
    def invalidate_prefix(self, cache: object, prefix: str) -> int: """Invalidate matching keys."""; keys = [k for k in getattr(cache, "_values", {}) if k.startswith(prefix)]; [cache.invalidate(k) for k in keys]; return len(keys)
