"""Scenario-specific virtual validation policy with explicit non-authorizing boundaries."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .virtual_adapters import VirtualFidelity, VirtualValidationPath, VirtualValidationPlan


class ValidationScenario(str, Enum):
    """Validation scenarios supported by the V1 evidence model."""

    LOGICAL_INTENT = "logical_intent"
    VENDOR_IMAGE_LAB = "vendor_image_lab"
    PHYSICAL_LAB = "physical_lab"
    CANDIDATE_COMMIT = "candidate_commit"
    UNSUPPORTED = "unsupported"


class ScenarioPolicyDecision(BaseModel):
    """Decision emitted by policy evaluation; it cannot grant production authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scenario: ValidationScenario
    supported: bool
    fidelity_label: VirtualFidelity
    required_evidence: tuple[str, ...] = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=500)
    production_change_authority: bool = False


class ScenarioValidationPolicy:
    """Map explicit validation path/fidelity pairs to bounded evidence decisions."""

    def evaluate(self, plan: VirtualValidationPlan) -> ScenarioPolicyDecision:
        if plan.fidelity_label is VirtualFidelity.UNSUPPORTED:
            return self._unsupported(plan, ValidationScenario.UNSUPPORTED, "The adapter explicitly marked this validation fidelity unsupported.")
        if plan.validation_path is VirtualValidationPath.DIGITAL_TWIN:
            if plan.fidelity_label is not VirtualFidelity.LOGICAL_INTENT_ONLY:
                return self._unsupported(plan, ValidationScenario.UNSUPPORTED, "Digital-twin validation must remain logical-intent-only.")
            return self._supported(plan, ValidationScenario.LOGICAL_INTENT, ("logical_intent_result", "artifact_hash_match", "target_facts_hash_match", "scope_hash_match"), "Logical intent validation is supported only as a non-emulating evidence path.")
        if plan.validation_path is VirtualValidationPath.LAB:
            if plan.fidelity_label is VirtualFidelity.PHYSICAL_LAB:
                return self._supported(plan, ValidationScenario.PHYSICAL_LAB, ("physical_lab_result", "artifact_hash_match", "target_facts_hash_match", "scope_hash_match"), "Physical-lab evidence is supported only when the approved laboratory result is separately recorded.")
            if plan.fidelity_label is VirtualFidelity.VENDOR_IMAGE_LAB:
                return self._supported(plan, ValidationScenario.VENDOR_IMAGE_LAB, ("vendor_image_result", "artifact_hash_match", "target_facts_hash_match", "scope_hash_match"), "Vendor-image lab evidence is supported only for the exact recorded image and scope.")
            return self._unsupported(plan, ValidationScenario.UNSUPPORTED, "Lab validation requires a vendor-image or physical-lab fidelity label.")
        if plan.validation_path is VirtualValidationPath.VENDOR_CANDIDATE_COMMIT and plan.fidelity_label is VirtualFidelity.CANDIDATE_COMMIT_EVIDENCE:
            return self._supported(plan, ValidationScenario.CANDIDATE_COMMIT, ("candidate_result", "artifact_hash_match", "target_facts_hash_match", "scope_hash_match"), "Candidate/commit evidence is bounded to the exact artifact, target facts, scope, and recorded result.")
        return self._unsupported(plan, ValidationScenario.UNSUPPORTED, "The validation path and fidelity label do not form a reviewed V1 scenario.")

    @staticmethod
    def _supported(plan: VirtualValidationPlan, scenario: ValidationScenario, evidence: tuple[str, ...], reason: str) -> ScenarioPolicyDecision:
        return ScenarioPolicyDecision(
            scenario=scenario,
            supported=True,
            fidelity_label=plan.fidelity_label,
            required_evidence=evidence,
            reason=reason,
            production_change_authority=False,
        )

    @staticmethod
    def _unsupported(plan: VirtualValidationPlan, scenario: ValidationScenario, reason: str) -> ScenarioPolicyDecision:
        return ScenarioPolicyDecision(
            scenario=scenario,
            supported=False,
            fidelity_label=plan.fidelity_label,
            required_evidence=("path_fidelity_review", "artifact_hash_match", "target_facts_hash_match", "scope_hash_match"),
            reason=reason,
            production_change_authority=False,
        )
