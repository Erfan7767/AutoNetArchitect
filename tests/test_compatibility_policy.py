from domain_packs.compatibility_policy import CompatibilityPolicy

def test_conflicting_production_packs_are_blocked():
    result = CompatibilityPolicy().evaluate(["banking", "hospital_clinical"])
    assert result["status"] == "blocked"
    assert result["conflicts"]
