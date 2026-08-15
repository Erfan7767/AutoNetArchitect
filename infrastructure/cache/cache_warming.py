"""Cache warming service."""
class CacheWarming:
    """Populate a cache from a mapping."""
    def warm(self, cache: object, values: dict[str, object]) -> int: """Populate values and return count."""; [cache.set(k, v) for k, v in values.items()]; return len(values)
