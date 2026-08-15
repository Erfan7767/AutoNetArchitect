from domain_packs.university_campus.acceptance_criteria import UniversityAcceptanceCriteria

def test_university_acceptance_requires_operations_and_evidence():
    result = UniversityAcceptanceCriteria().design({"sector": "university"})["artifact"]
    assert result["review_threshold"] == "enhanced_domain_review"
    assert "operations_integration" in result["production_claim_requires"]
