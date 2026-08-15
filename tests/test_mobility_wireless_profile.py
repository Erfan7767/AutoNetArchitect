from domain_packs.hospital_clinical.mobility_wireless_profile import MobilityWirelessProfile

def test_mobility_wireless_profile_imports_and_scope():
    result = MobilityWirelessProfile().design({"sector": "hospital_clinical"})
    assert result["scope_guard"]["applicable"] is True
