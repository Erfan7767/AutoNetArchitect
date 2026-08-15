from importlib import import_module


Generator = getattr(import_module("config_generators.paloalto.panos_generator"), "PANOSGenerator")


def test_panos_generator_produces_traceable_versioned_artifact():
    result = Generator().generate({
        "device": {"device_id": "panos-1", "platform": "panos", "os_version": "1.0"},
        "decision_ids": ["decision-panos"],
        "capability_evidence": {"routing": {"verification_state": "verified", "evidence_ids": ["evidence-routing"], "platform": "panos"}},
        "features": [{"feature": "routing", "capability": "routing", "commands": ["exact command for panos"], "command_source_ids": ["source-cli-panos"]}],
        "secret_references": ["secret://devices/panos-1/credential"],
    })
    artifact = result.artifact
    assert artifact.status == "generated"
    assert artifact.vendor == "PaloAlto"
    assert artifact.platform == "panos"
    assert artifact.commands == ("exact command for panos",)
    assert artifact.rendered_config.strip() == "exact command for panos"
    assert artifact.decision_ids == ("decision-panos",)
    assert artifact.secret_references == ("secret://devices/panos-1/credential",)
    assert artifact.artifact_hash


def test_panos_generator_logs_unsupported_feature_without_substitution():
    result = Generator().generate({"device_id": "panos-2", "features": [{"feature": "unknown", "capability": "unknown", "commands": ["must-not-be-emitted"]}]})
    assert result.artifact.status == "blocked_unsupported_features"
    assert result.artifact.rendered_config == ""
    assert result.artifact.commands == ()
    assert result.artifact.unsupported_log
