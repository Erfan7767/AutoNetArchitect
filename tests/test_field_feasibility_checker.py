"""Field reality test."""
from field_reality.site_model import SiteModel
from field_reality.field_feasibility_checker import FieldFeasibilityChecker
def test_pending_when_site_unknown():
    site = SiteModel("s", "office"); result = FieldFeasibilityChecker().check(site, True, proposed_rack_units=10); assert result.status == "blocked_pending_site_data" and not result.physical_recommendation_allowed
