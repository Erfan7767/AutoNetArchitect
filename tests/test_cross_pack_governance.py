from domain_packs.cross_pack_governance import CrossPackGovernance

def test_governance_requires_review_when_not_complete():
    result = CrossPackGovernance().govern({"active_packs": ["banking"], "review_required": True, "review_completed": False})
    assert result["status"] == "review_required"
