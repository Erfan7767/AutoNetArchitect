"""Retry policy."""
from dataclasses import dataclass
@dataclass(frozen=True)
class RetryPolicy:
    """Retry count and delay policy."""
    attempts: int = 3
    delay_seconds: float = 0.1
