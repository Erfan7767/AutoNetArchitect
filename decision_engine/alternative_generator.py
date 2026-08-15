"""Alternative generation from explicit option data."""
from __future__ import annotations
from .decision_context import Alternative
class AlternativeGenerator:
    """Generate only named alternatives; never invent unavailable evidence."""
    def from_options(self, options: list[dict[str, object]]) -> list[Alternative]:
        """Convert option records into validated alternatives."""
        return [Alternative(name=str(item["name"]), attributes={str(k): float(v) for k, v in dict(item.get("attributes", {})).items()}, evidence=list(item.get("evidence", [])), assumptions=list(item.get("assumptions", []))) for item in options if item.get("name")]
