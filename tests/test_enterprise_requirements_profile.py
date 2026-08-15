from domain_packs.enterprise_corporate.requirements_profile import EnterpriseRequirementsProfile

def test_requirements_are_explicit():
    result = EnterpriseRequirementsProfile().design({"sector": "enterprise_corporate"})
    assert "site_inventory" in result["artifact"]["mandatory_inputs"]
