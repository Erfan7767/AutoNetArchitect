from pathlib import Path

from config_validators.validation_orchestrator import ValidationOrchestrator
from config_validators.models import ValidationStatus


def test_orchestrator_valid_fixture_is_warning_scoped_and_gate_blocked_until_clean():
    text = Path("tests/fixtures/valid_configs/cisco_ios_xe_valid.txt").read_text()
    report = ValidationOrchestrator().validate(text, "Cisco", "IOS XE", "C9300", "17.15")
    assert report.overall_status is ValidationStatus.PASSED_WITH_WARNINGS
    assert not report.errors
    assert report.coverage_percentage >= 0
    assert report.deployment_gate == "blocked"


def test_orchestrator_invalid_fixture_fails_pre_deployment_gate():
    text = Path("tests/fixtures/invalid_configs/cisco_ios_xe_invalid.txt").read_text()
    report = ValidationOrchestrator().validate(text, "Cisco", "IOS XE")
    gate = ValidationOrchestrator.pre_deployment_gate(report)
    assert report.overall_status is ValidationStatus.FAILED
    assert gate.allowed is False
    assert report.errors


def test_orchestrator_consumes_blocked_device_config_artifact():
    from config_generators.base_generator import DeviceConfig

    artifact = DeviceConfig("1.0", "artifact-1", "edge-1", "Cisco", "IOS XE", "17.15", "blocked_unsupported_features", "", (), ({"feature": "ospf"},), (), (), (), (), (), "", "")
    report = ValidationOrchestrator().validate_artifact(artifact)
    assert report.overall_status is ValidationStatus.FAILED
    assert any(item.code == "GENERATION_ARTIFACT_BLOCKED" for item in report.errors)


def test_orchestrator_consumes_feature_guard_failures():
    from config_generators.feature_guards import FeatureGuards

    text = Path("tests/fixtures/valid_configs/cisco_ios_xe_valid.txt").read_text()
    report = ValidationOrchestrator().validate(
        text,
        "Cisco",
        "IOS XE",
        context={
            "feature_guard": FeatureGuards(),
            "feature_requests": [{"feature": "ospf", "capability": "routing.ospf", "commands": ["router ospf 10"], "decision_ids": ["decision-1"], "command_source_ids": ["source-1"]}],
            "capability_evidence": {},
            "license_evidence": {},
        },
    )
    assert any(item.code == "FEATURE_GUARD_BLOCKED" for item in report.errors)
