from domain_packs.enterprise_corporate.acceptance_criteria import EnterpriseAcceptanceCriteria

def test_acceptance_requires_evidence():
    result = EnterpriseAcceptanceCriteria().design({"sector": "enterprise_corporate"})
    assert result["artifact"]["minimum_status"] == "all_applicable_criteria_verified"
    assert "formal_proof_status" in result["artifact"]["production_claim_requires"]
