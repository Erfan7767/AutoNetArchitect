from domain_packs.hospital_clinical.resilience_profile import HospitalResilienceProfile

def test_resilience_profile_imports_and_scope():
    result = HospitalResilienceProfile().design({"sector": "hospital_clinical"})
    assert result["scope_guard"]["applicable"] is True
