from domain_packs.university_campus.dormitory_access_patterns import DormitoryAccessPatterns

def test_dormitory_access_patterns_imports_and_scope():
    result = DormitoryAccessPatterns().design({"sector": "university_campus"})
    assert result["scope_guard"]["applicable"] is True
