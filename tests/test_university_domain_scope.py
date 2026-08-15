from domain_packs.university_campus.domain_scope import UniversityCampusPack

def test_university_scope_is_explicit_and_diverse():
    result = UniversityCampusPack().design({"sector": "university_campus"})
    assert result["scope_guard"]["applicable"] is True
    assert "research" in result["artifact"]["functional_domains"]
    assert UniversityCampusPack().design({"sector": "banking"})["scope_guard"]["status"] == "out_of_scope"
