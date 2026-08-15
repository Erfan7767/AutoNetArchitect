from domain_packs.banking.acceptance_criteria import BankingAcceptanceCriteria

def test_banking_acceptance_has_enhanced_review():
    result = BankingAcceptanceCriteria().design({"sector": "banking"})["artifact"]
    assert result["review_threshold"] == "enhanced_manual_review"
    assert result["compliance_readiness_claim"] == "not_allowed_without_authoritative_evidence_and_scope"
