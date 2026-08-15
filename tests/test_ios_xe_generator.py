from importlib import import_module


Generator = getattr(import_module("config_generators.cisco.ios_xe_generator"), "IOSXEGenerator")


def test_ios_xe_generator_produces_traceable_versioned_artifact():
    result = Generator().generate({
        "device": {"device_id": "ios_xe-1", "platform": "ios_xe", "os_version": "1.0"},
        "decision_ids": ["decision-ios_xe"],
        "capability_evidence": {"routing": {"verification_state": "verified", "evidence_ids": ["evidence-routing"], "platform": "ios_xe"}},
        "features": [{"feature": "routing", "capability": "routing", "commands": ["exact command for ios_xe"], "command_source_ids": ["source-cli-ios_xe"]}],
        "secret_references": ["secret://devices/ios_xe-1/credential"],
    })
    artifact = result.artifact
    assert artifact.status == "generated"
    assert artifact.vendor == "Cisco"
    assert artifact.platform == "ios_xe"
    assert artifact.commands == ("exact command for ios_xe",)
    assert artifact.rendered_config.strip() == "exact command for ios_xe"
    assert artifact.decision_ids == ("decision-ios_xe",)
    assert artifact.secret_references == ("secret://devices/ios_xe-1/credential",)
    assert artifact.artifact_hash


def test_ios_xe_generator_logs_unsupported_feature_without_substitution():
    result = Generator().generate({"device_id": "ios_xe-2", "features": [{"feature": "unknown", "capability": "unknown", "commands": ["must-not-be-emitted"]}]})
    assert result.artifact.status == "blocked_unsupported_features"
    assert result.artifact.rendered_config == ""
    assert result.artifact.commands == ()
    assert result.artifact.unsupported_log
