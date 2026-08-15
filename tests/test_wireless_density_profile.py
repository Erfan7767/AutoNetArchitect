from domain_packs.university_campus.wireless_density_profile import WirelessDensityProfile

def test_wireless_density_requires_evidence_levels():
    result = WirelessDensityProfile().design({"sector": "university"})["artifact"]
    assert "lecture_hall" in result["density_profiles"]
    assert "survey_backed_production_validation" in result["planning_modes"]
