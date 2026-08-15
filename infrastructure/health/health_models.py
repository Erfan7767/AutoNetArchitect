"""Health result models."""
from dataclasses import dataclass
@dataclass(frozen=True)
class HealthResult:
    """Health status for one component."""
    component: str
    healthy: bool
    detail: str = ""
