from importlib import import_module


Generator = getattr(import_module("config_generators.cisco.wlc_generator"), "WLCGenerator")


def test_wlc_generator_produces_traceable_versioned_artifact():
    result = Generator().generate({
        "device": {"device_id": "wlc-1", "platform": "wlc", "os_version": "1.0"},
        "decision_ids": ["decision-wlc"],
        "capability_evidence": {"routing": {"verification_state": "verified", "evidence_ids": ["evidence-routing"], "platform": "wlc"}},
        "features": [{"feature": "routing", "capability": "routing", "commands": ["exact command for wlc"], "command_source_ids": ["source-cli-wlc"]}],
        "secret_references": ["secret://devices/wlc-1/credential"],
    })
    artifact = result.artifact
    assert artifact.status == "generated"
    assert artifact.vendor == "Cisco"
    assert artifact.platform == "wlc"
    assert artifact.commands == ("exact command for wlc",)
    assert artifact.rendered_config.strip() == "exact command for wlc"
    assert artifact.decision_ids == ("decision-wlc",)
    assert artifact.secret_references == ("secret://devices/wlc-1/credential",)
    assert artifact.artifact_hash


def test_wlc_generator_logs_unsupported_feature_without_substitution():
    result = Generator().generate({"device_id": "wlc-2", "features": [{"feature": "unknown", "capability": "unknown", "commands": ["must-not-be-emitted"]}]})
    assert result.artifact.status == "blocked_unsupported_features"
    assert result.artifact.rendered_config == ""
    assert result.artifact.commands == ()
    assert result.artifact.unsupported_log
