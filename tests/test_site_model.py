"""Field reality test."""
from field_reality.site_model import SiteModel
def test_unknowns_are_missing():
    assert "available_rack_units" in SiteModel("s", "office").missing_fields()
