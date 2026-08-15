from config_generators.feature_guards import FeatureGuards


def test_guard_allows_only_traceable_exact_commands():
    result = FeatureGuards().evaluate(
        {"feature": "ospf", "capability": "routing", "commands": ["router ospf 1"], "required_license": "advanced", "command_source_ids": ["src-cli"], "decision_ids": ["dec-routing"]},
        {"routing": {"verification_state": "verified", "evidence_ids": ["ev-routing"], "platform": "ios_xe"}},
        {"advanced": {"verification_state": "verified", "evidence_ids": ["ev-license"], "production_eligible": True}},
        "ios_xe",
        "17.9",
    )
    assert result.allowed is True
    assert result.capability_evidence_ids == ("ev-routing",)


def test_guard_rejects_missing_evidence_and_commands():
    result = FeatureGuards().evaluate({"feature": "ospf", "capability": "routing", "commands": []}, {}, {}, "ios_xe", "17.9")
    assert result.allowed is False
    assert "capability_evidence_missing_unverified_expired_or_revoked" in result.reasons
    assert "exact_commands_missing_or_not_a_string_list" in result.reasons
    assert "design_decision_reference_missing" in result.reasons
