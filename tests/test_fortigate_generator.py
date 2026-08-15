from importlib import import_module


Generator = getattr(import_module("config_generators.fortinet.fortigate_generator"), "FortiGateGenerator")


def test_fortigate_generator_produces_traceable_versioned_artifact():
    result = Generator().generate({
        "device": {"device_id": "fortigate-1", "platform": "fortigate", "os_version": "1.0"},
        "decision_ids": ["decision-fortigate"],
        "capability_evidence": {"routing": {"verification_state": "verified", "evidence_ids": ["evidence-routing"], "platform": "fortigate"}},
        "features": [{"feature": "routing", "capability": "routing", "commands": ["exact command for fortigate"], "command_source_ids": ["source-cli-fortigate"]}],
        "secret_references": ["secret://devices/fortigate-1/credential"],
    })
    artifact = result.artifact
    assert artifact.status == "generated"
    assert artifact.vendor == "Fortinet"
    assert artifact.platform == "fortigate"
    assert artifact.commands == ("exact command for fortigate",)
    assert artifact.rendered_config.strip() == "exact command for fortigate"
    assert artifact.decision_ids == ("decision-fortigate",)
    assert artifact.secret_references == ("secret://devices/fortigate-1/credential",)
    assert artifact.artifact_hash


def test_fortigate_generator_logs_unsupported_feature_without_substitution():
    result = Generator().generate({"device_id": "fortigate-2", "features": [{"feature": "unknown", "capability": "unknown", "commands": ["must-not-be-emitted"]}]})
    assert result.artifact.status == "blocked_unsupported_features"
    assert result.artifact.rendered_config == ""
    assert result.artifact.commands == ()
    assert result.artifact.unsupported_log
