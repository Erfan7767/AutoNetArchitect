from domain_packs.hospital_clinical.requirements_profile import HospitalRequirementsProfile

def test_requirements_profile_imports_and_scope():
    result = HospitalRequirementsProfile().design({"sector": "hospital_clinical"})
    assert result["scope_guard"]["applicable"] is True
