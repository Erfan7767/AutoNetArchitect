from datetime import date

from change_management import ChangeRequest, StandardChange, StandardChangeCatalog


def _entry():
    return StandardChange("STD-1", "Add VLAN", "single switch", "single access switch only", "low", "governance", date(2026, 1, 1), date(2027, 1, 1), "add_vlan", "add_vlan", "add_vlan")


def test_standard_change_catalog_registers_and_tracks_usage():
    catalog = StandardChangeCatalog([_entry()])
    request = ChangeRequest("CHG-22", "VLAN", "Detailed", "alice")
    assert catalog.eligible(request, today=date(2026, 6, 1))[0].catalog_id == "STD-1"
    catalog.record_use("STD-1", successful=True)
    assert catalog.get("STD-1").usage_count == 1
    assert catalog.due_for_review(today=date(2028, 1, 1))[0].catalog_id == "STD-1"


def test_standard_change_catalog_rejects_non_low_risk():
    rejected = False
    try:
        StandardChangeCatalog([StandardChange("STD-2", "High", "x", "x", "high", "gov", date(2026, 1, 1), date(2027, 1, 1), "x", "x", "x")])
    except ValueError:
        rejected = True
    assert rejected is True
