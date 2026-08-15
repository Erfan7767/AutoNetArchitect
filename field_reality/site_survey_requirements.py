"""Site survey requirement generation."""
from __future__ import annotations
class SiteSurveyRequirements:
    """Produce mandatory measurements before physical recommendation."""
    REQUIRED = ["room_dimensions", "rack_units", "power_feeds", "ups_status", "hvac_measurement", "pathway_capacity", "grounding_test", "access_window", "safety_permits"]
    def required_for(self, site: object, proposed_rack_units: int = 0, proposed_feeds: int = 0) -> list[str]:
        """Return unresolved requirements based on site data and proposed load."""
        missing = list(getattr(site, "missing_fields")())
        if proposed_rack_units and (getattr(site, "available_rack_units", None) is None or proposed_rack_units > site.available_rack_units): missing.append("rack_capacity_verification")
        if proposed_feeds and (getattr(site, "available_power_feeds", None) is None or proposed_feeds > site.available_power_feeds): missing.append("power_feed_verification")
        return sorted(set(missing))
