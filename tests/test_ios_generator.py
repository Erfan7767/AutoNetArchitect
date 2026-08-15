from importlib import import_module


Generator = getattr(import_module("config_generators.cisco.ios_generator"), "IOSGenerator")


def test_ios_generator_produces_traceable_versioned_artifact():
    result = Generator().generate({
        "device": {"device_id": "ios-1", "platform": "ios", "os_version": "1.0"},
        "decision_ids": ["decision-ios"],
        "capability_evidence": {"routing": {"verification_state": "verified", "evidence_ids": ["evidence-routing"], "platform": "ios"}},
        "features": [{"feature": "routing", "capability": "routing", "commands": ["exact command for ios"], "command_source_ids": ["source-cli-ios"]}],
        "secret_references": ["secret://devices/ios-1/credential"],
    })
    artifact = result.artifact
    assert artifact.status == "generated"
    assert artifact.vendor == "Cisco"
    assert artifact.platform == "ios"
    assert artifact.commands == ("exact command for ios",)
    assert artifact.rendered_config.strip() == "exact command for ios"
    assert artifact.decision_ids == ("decision-ios",)
    assert artifact.secret_references == ("secret://devices/ios-1/credential",)
    assert artifact.artifact_hash


def test_ios_generator_logs_unsupported_feature_without_substitution():
    result = Generator().generate({"device_id": "ios-2", "features": [{"feature": "unknown", "capability": "unknown", "commands": ["must-not-be-emitted"]}]})
    assert result.artifact.status == "blocked_unsupported_features"
    assert result.artifact.rendered_config == ""
    assert result.artifact.commands == ()
    assert result.artifact.unsupported_log
