"""Windows-facing preparation of a bounded local virtual-validation review plan."""

from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel, ConfigDict, Field

from site_agent.coordination import AgentAssignment, AgentRole
from site_agent.discovery_coordination import CoordinatedDiscoveryResult, DiscoveryBatchResult
from site_agent.evidence_handoff import DesignEvidenceHandoff
from site_agent.exact_capability import ExactCapabilityAssessor, ExactCapabilityEvidence
from site_agent.models import DiscoveryResult, DiscoveryState
from site_agent.vendor_support import SupportDecision
from site_agent.virtual_adapters import LabValidationAdapter, VirtualValidationPlan

from .virtual_validation import LocalVirtualValidationController
from .workspace import WindowsWorkspace


class LocalValidationReviewDraft(BaseModel):
    """Human-supplied non-secret references required before a local validation plan can be prepared."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_hash: str = Field(min_length=1, max_length=160)
    platform_family: str = Field(min_length=1, max_length=120)
    exact_model_evidence_reference: str = Field(min_length=1, max_length=200)
    license_evidence_reference: str = Field(min_length=1, max_length=200)
    configuration_path_evidence_reference: str = Field(min_length=1, max_length=200)
    requested_capabilities: tuple[str, ...] = ()


class WindowsValidationReviewController:
    """Prepare local lab-validation review plans from selected discovered facts without running a lab or production action."""

    def __init__(self, workspace: WindowsWorkspace, assessor: ExactCapabilityAssessor | None = None) -> None:
        """Use the same local workspace and exact capability policy as the broader site-agent workflow."""

        self._workspace = workspace
        self._assessor = assessor or ExactCapabilityAssessor()

    def prepare_plan(self, discovery_result: DiscoveryResult, draft: LocalValidationReviewDraft) -> VirtualValidationPlan:
        """Return a queued lab-validation plan only for a scope-bound, exactly capable discovered device."""

        scope = self._workspace.load_scope()
        if scope is None:
            raise PermissionError("Save a human-approved local scope before preparing virtual validation.")
        if discovery_result.state is not DiscoveryState.DISCOVERED or discovery_result.facts is None:
            raise ValueError("Virtual validation requires one selected discovery result with observed device facts.")
        if not scope.authorizes(discovery_result.target):
            raise PermissionError("The selected discovery result is outside the currently approved local scope.")
        facts_hash = self._facts_hash(discovery_result)
        assessment = self._assessor.assess(ExactCapabilityEvidence(
            facts=discovery_result.facts,
            protocol=discovery_result.target.protocol,
            platform_family=draft.platform_family,
            exact_model_evidence_reference=draft.exact_model_evidence_reference,
            license_evidence_reference=draft.license_evidence_reference,
            configuration_path_evidence_reference=draft.configuration_path_evidence_reference,
            requested_capabilities=draft.requested_capabilities,
        ))
        if assessment.decision is not SupportDecision.CONFIGURATION_SUPPORTED or assessment.vendor_family is None:
            raise ValueError(f"Exact capability evidence does not support a local validation plan: {assessment.reason}")
        scope_hash = scope.evidence_hash()
        assignment = AgentAssignment(
            agent_id="windows-local-review",
            role=AgentRole.AUTHORIZED_DISCOVERY,
            site_id=scope.site_id,
            scope_hash=scope_hash,
            authority_reference=scope.approval_reference,
        )
        batch = DiscoveryBatchResult(
            site_id=scope.site_id,
            scope_hash=scope_hash,
            results=(CoordinatedDiscoveryResult(assignment=assignment, result=discovery_result, scope_hash=scope_hash),),
        )
        handoff = DesignEvidenceHandoff(
            site_id=scope.site_id,
            scope_hash=scope_hash,
            requirements_hash="human-reviewed-local-requirements",
            design_artifact_hash=draft.artifact_hash,
            target_facts_hash=facts_hash,
            discovery_evidence_reference=f"local-discovery:{discovery_result.target.address}",
            capability_assessment_reference=f"local-capability:{assessment.vendor_family.value}:{facts_hash}",
            capability_assessment=assessment,
        )
        return LocalVirtualValidationController(self._workspace).prepare(batch, handoff, LabValidationAdapter(assessment.vendor_family))

    @staticmethod
    def _facts_hash(result: DiscoveryResult) -> str:
        """Hash only observed device facts so the validation plan cannot drift from the reviewed discovery record."""

        if result.facts is None:
            raise ValueError("Observed device facts are required.")
        payload = json.dumps(result.facts.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
