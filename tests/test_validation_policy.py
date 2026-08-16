from site_agent.validation_policy import ScenarioValidationPolicy, ValidationScenario
from site_agent.vendor_support import VendorFamily
from site_agent.virtual_adapters import (
    DigitalTwinValidationAdapter,
    LabValidationAdapter,
    VirtualFidelity,
    VirtualValidationPath,
    VirtualValidationPlan,
)


def _plan(path: VirtualValidationPath, fidelity: VirtualFidelity) -> VirtualValidationPlan:
    return VirtualValidationPlan(
        vendor_family=VendorFamily.CISCO,
        validation_path=path,
        adapter_kind="test-adapter",
        fidelity_label=fidelity,
        artifact_hash="artifact-hash",
        target_facts_hash="facts-hash",
        scope_hash="scope-hash",
        evidence_requirements=("virtual_result_record",),
        limitation="Test plan is evidence only.",
    )


def test_logical_intent_policy_is_supported_but_non_authorizing() -> None:
    decision = ScenarioValidationPolicy().evaluate(_plan(VirtualValidationPath.DIGITAL_TWIN, VirtualFidelity.LOGICAL_INTENT_ONLY))
    assert decision.supported is True
    assert decision.scenario is ValidationScenario.LOGICAL_INTENT
    assert decision.production_change_authority is False
    assert "logical_intent_result" in decision.required_evidence


def test_lab_policy_distinguishes_vendor_image_and_physical_lab() -> None:
    policy = ScenarioValidationPolicy()
    image = policy.evaluate(_plan(VirtualValidationPath.LAB, VirtualFidelity.VENDOR_IMAGE_LAB))
    physical = policy.evaluate(_plan(VirtualValidationPath.LAB, VirtualFidelity.PHYSICAL_LAB))
    assert image.scenario is ValidationScenario.VENDOR_IMAGE_LAB
    assert physical.scenario is ValidationScenario.PHYSICAL_LAB
    assert image.production_change_authority is False
    assert physical.production_change_authority is False


def test_candidate_commit_policy_requires_candidate_fidelity() -> None:
    policy = ScenarioValidationPolicy()
    decision = policy.evaluate(_plan(VirtualValidationPath.VENDOR_CANDIDATE_COMMIT, VirtualFidelity.CANDIDATE_COMMIT_EVIDENCE))
    assert decision.supported is True
    assert decision.scenario is ValidationScenario.CANDIDATE_COMMIT
    assert "candidate_result" in decision.required_evidence


def test_mismatched_path_and_fidelity_is_unsupported() -> None:
    policy = ScenarioValidationPolicy()
    decision = policy.evaluate(_plan(VirtualValidationPath.LAB, VirtualFidelity.LOGICAL_INTENT_ONLY))
    assert decision.supported is False
    assert decision.scenario is ValidationScenario.UNSUPPORTED
    assert decision.production_change_authority is False
