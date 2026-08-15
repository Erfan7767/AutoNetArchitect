from domain_packs.hospital_clinical.imaging_pacs_profile import ImagingPACSProfile

def test_imaging_pacs_profile_imports_and_scope():
    result = ImagingPACSProfile().design({"sector": "hospital_clinical"})
    assert result["scope_guard"]["applicable"] is True
