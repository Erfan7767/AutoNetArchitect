from importlib import import_module


Generator = getattr(import_module("config_generators.huawei.vrp_generator"), "VRPGenerator")


def test_vrp_generator_produces_traceable_versioned_artifact():
    result = Generator().generate({
        "device": {"device_id": "vrp-1", "platform": "vrp", "os_version": "1.0"},
        "decision_ids": ["decision-vrp"],
        "capability_evidence": {"routing": {"verification_state": "verified", "evidence_ids": ["evidence-routing"], "platform": "vrp"}},
        "features": [{"feature": "routing", "capability": "routing", "commands": ["exact command for vrp"], "command_source_ids": ["source-cli-vrp"]}],
        "secret_references": ["secret://devices/vrp-1/credential"],
    })
    artifact = result.artifact
    assert artifact.status == "generated"
    assert artifact.vendor == "Huawei"
    assert artifact.platform == "vrp"
    assert artifact.commands == ("exact command for vrp",)
    assert artifact.rendered_config.strip() == "exact command for vrp"
    assert artifact.decision_ids == ("decision-vrp",)
    assert artifact.secret_references == ("secret://devices/vrp-1/credential",)
    assert artifact.artifact_hash


def test_vrp_generator_logs_unsupported_feature_without_substitution():
    result = Generator().generate({"device_id": "vrp-2", "features": [{"feature": "unknown", "capability": "unknown", "commands": ["must-not-be-emitted"]}]})
    assert result.artifact.status == "blocked_unsupported_features"
    assert result.artifact.rendered_config == ""
    assert result.artifact.commands == ()
    assert result.artifact.unsupported_log
