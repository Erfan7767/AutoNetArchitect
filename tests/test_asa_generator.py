from importlib import import_module


Generator = getattr(import_module("config_generators.cisco.asa_generator"), "ASAGenerator")


def test_asa_generator_produces_traceable_versioned_artifact():
    result = Generator().generate({
        "device": {"device_id": "asa-1", "platform": "asa", "os_version": "1.0"},
        "decision_ids": ["decision-asa"],
        "capability_evidence": {"routing": {"verification_state": "verified", "evidence_ids": ["evidence-routing"], "platform": "asa"}},
        "features": [{"feature": "routing", "capability": "routing", "commands": ["exact command for asa"], "command_source_ids": ["source-cli-asa"]}],
        "secret_references": ["secret://devices/asa-1/credential"],
    })
    artifact = result.artifact
    assert artifact.status == "generated"
    assert artifact.vendor == "Cisco"
    assert artifact.platform == "asa"
    assert artifact.commands == ("exact command for asa",)
    assert artifact.rendered_config.strip() == "exact command for asa"
    assert artifact.decision_ids == ("decision-asa",)
    assert artifact.secret_references == ("secret://devices/asa-1/credential",)
    assert artifact.artifact_hash


def test_asa_generator_logs_unsupported_feature_without_substitution():
    result = Generator().generate({"device_id": "asa-2", "features": [{"feature": "unknown", "capability": "unknown", "commands": ["must-not-be-emitted"]}]})
    assert result.artifact.status == "blocked_unsupported_features"
    assert result.artifact.rendered_config == ""
    assert result.artifact.commands == ()
    assert result.artifact.unsupported_log
