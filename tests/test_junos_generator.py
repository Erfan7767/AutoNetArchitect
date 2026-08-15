from importlib import import_module


Generator = getattr(import_module("config_generators.juniper.junos_generator"), "JunosGenerator")


def test_junos_generator_produces_traceable_versioned_artifact():
    result = Generator().generate({
        "device": {"device_id": "junos-1", "platform": "junos", "os_version": "1.0"},
        "decision_ids": ["decision-junos"],
        "capability_evidence": {"routing": {"verification_state": "verified", "evidence_ids": ["evidence-routing"], "platform": "junos"}},
        "features": [{"feature": "routing", "capability": "routing", "commands": ["exact command for junos"], "command_source_ids": ["source-cli-junos"]}],
        "secret_references": ["secret://devices/junos-1/credential"],
    })
    artifact = result.artifact
    assert artifact.status == "generated"
    assert artifact.vendor == "Juniper"
    assert artifact.platform == "junos"
    assert artifact.commands == ("exact command for junos",)
    assert artifact.rendered_config.strip() == "exact command for junos"
    assert artifact.decision_ids == ("decision-junos",)
    assert artifact.secret_references == ("secret://devices/junos-1/credential",)
    assert artifact.artifact_hash


def test_junos_generator_logs_unsupported_feature_without_substitution():
    result = Generator().generate({"device_id": "junos-2", "features": [{"feature": "unknown", "capability": "unknown", "commands": ["must-not-be-emitted"]}]})
    assert result.artifact.status == "blocked_unsupported_features"
    assert result.artifact.rendered_config == ""
    assert result.artifact.commands == ()
    assert result.artifact.unsupported_log
