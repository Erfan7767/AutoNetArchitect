"""Cache policy."""
from dataclasses import dataclass
@dataclass(frozen=True)
class CachePolicy:
    """TTL and invalidation policy."""
    ttl_seconds: int = 300
