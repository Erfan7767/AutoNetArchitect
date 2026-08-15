"""Capacity planning output."""
from __future__ import annotations
from .scaling_engine import ScalingEngine
class CapacityPlanner:
    """Plan user and address capacity."""
    def __init__(self, scaling: ScalingEngine | None = None) -> None: self.scaling = scaling or ScalingEngine()
    def plan(self, users: int, growth: float, years: int = 3) -> dict[str, object]:
        """Return capacity numbers and their assumptions."""
        return {"current_users": users, "planned_users": round(self.scaling.scale(users, growth, years)), "years": years, "source": "growth_assumption"}
