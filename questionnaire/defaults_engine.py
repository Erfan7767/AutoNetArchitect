"""Context-aware defaults that never override human mandatory fields."""
from __future__ import annotations
from typing import Any
class DefaultsEngine:
    """Suggest defaults with explicit provenance."""
    def suggest(self, answers: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Return only defensible suggestions and their provenance."""
        suggestions: dict[str, dict[str, Any]] = {}
        if "redundancy_level" not in answers and answers.get("high_availability") is False: suggestions["redundancy_level"] = {"value": 0, "source": "derived_from_availability"}
        if "environment_type" not in answers and answers.get("existing_inventory_required") is True: suggestions["environment_type"] = {"value": "brownfield", "source": "derived_from_inventory"}
        if "site_count" not in answers and answers.get("wan_required") is False: suggestions["site_count"] = {"value": 1, "source": "minimal_single_site_assumption"}
        return suggestions
