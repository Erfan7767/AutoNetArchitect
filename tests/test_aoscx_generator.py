from importlib import import_module


Generator = getattr(import_module("config_generators.aruba.aoscx_generator"), "AOSCXGenerator")


def test_aoscx_generator_produces_traceable_versioned_artifact():
    result = Generator().generate({
        "device": {"device_id": "aoscx-1", "platform": "aoscx", "os_version": "1.0"},
        "decision_ids": ["decision-aoscx"],
        "capability_evidence": {"routing": {"verification_state": "verified", "evidence_ids": ["evidence-routing"], "platform": "aoscx"}},
        "features": [{"feature": "routing", "capability": "routing", "commands": ["exact command for aoscx"], "command_source_ids": ["source-cli-aoscx"]}],
        "secret_references": ["secret://devices/aoscx-1/credential"],
    })
    artifact = result.artifact
    assert artifact.status == "generated"
    assert artifact.vendor == "Aruba"
    assert artifact.platform == "aoscx"
    assert artifact.commands == ("exact command for aoscx",)
    assert artifact.rendered_config.strip() == "exact command for aoscx"
    assert artifact.decision_ids == ("decision-aoscx",)
    assert artifact.secret_references == ("secret://devices/aoscx-1/credential",)
    assert artifact.artifact_hash


def test_aoscx_generator_logs_unsupported_feature_without_substitution():
    result = Generator().generate({"device_id": "aoscx-2", "features": [{"feature": "unknown", "capability": "unknown", "commands": ["must-not-be-emitted"]}]})
    assert result.artifact.status == "blocked_unsupported_features"
    assert result.artifact.rendered_config == ""
    assert result.artifact.commands == ()
    assert result.artifact.unsupported_log
