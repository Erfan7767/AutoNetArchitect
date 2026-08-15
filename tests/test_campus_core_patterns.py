from domain_packs.university_campus.campus_core_patterns import CampusCorePatterns

def test_campus_core_patterns_imports_and_scope():
    result = CampusCorePatterns().design({"sector": "university_campus"})
    assert result["scope_guard"]["applicable"] is True
