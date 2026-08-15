"""Capacity scaling and brownfield/greenfield classification."""
from __future__ import annotations
class ScalingEngine:
    """Calculate growth-aware capacity."""
    def classify_environment(self, answers: dict[str, object]) -> str:
        """Classify as brownfield when existing assets or migration exist."""
        return "brownfield" if answers.get("existing_inventory_required") or answers.get("migration_required") else "greenfield"
    def scale(self, current: float, annual_growth: float, years: int = 3, safety_factor: float = 1.2) -> float:
        """Return growth and safety-factor adjusted capacity."""
        if current < 0 or annual_growth < 0 or years < 0: raise ValueError("scaling inputs must be non-negative")
        return current * ((1 + annual_growth) ** years) * safety_factor
