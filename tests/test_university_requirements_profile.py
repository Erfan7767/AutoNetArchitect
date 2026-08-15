from domain_packs.university_campus.requirements_profile import UniversityRequirementsProfile

def test_university_profiles_are_not_collapsed():
    result = UniversityRequirementsProfile().design({"sector": "university"})["artifact"]
    assert set(result["functional_profiles"]) == {"academic", "administrative", "research", "residential"}
