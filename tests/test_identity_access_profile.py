from domain_packs.university_campus.identity_access_profile import IdentityAccessProfile

def test_identity_access_profile_imports_and_scope():
    result = IdentityAccessProfile().design({"sector": "university_campus"})
    assert result["scope_guard"]["applicable"] is True
