from domain_packs.banking.requirements_profile import BankingRequirementsProfile

def test_banking_requires_high_assurance_inputs():
    result = BankingRequirementsProfile().design({"sector": "banking"})
    assert "privileged_roles_and_admin_paths" in result["artifact"]["mandatory_inputs"]
    assert result["artifact"]["unresolved_input_policy"] == "block_or_manual_review_not_silent_defaulting"
