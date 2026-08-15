"""Cache models."""
from dataclasses import dataclass
@dataclass(frozen=True)
class CacheEntry:
    """A cache value and expiration metadata."""
    key: str
    value: object
