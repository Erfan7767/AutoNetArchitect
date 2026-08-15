from domain_packs.university_campus.research_network_patterns import ResearchNetworkPatterns

def test_research_exceptions_have_ownership_and_expiry():
    result = ResearchNetworkPatterns().design({"sector": "university"})["artifact"]
    assert "named_owner" in result["exception_controls"]
    assert "expiry_date" in result["exception_controls"]
