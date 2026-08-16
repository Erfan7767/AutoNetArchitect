"""Evidence-bound handoff from discovery coordination to virtual validation planning."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .coordination import CoordinationStage, MultiAgentResponsibilityModel
from .discovery_coordination import DiscoveryBatchResult
from .virtual_adapters import VirtualValidationPathAdapter, VirtualValidationPlan


class DesignEvidenceHandoff(BaseModel):
    """Immutable references required to submit a design artifact for validation review."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    site_id: str = Field(min_length=1, max_length=160)
    scope_hash: str = Field(min_length=1, max_length=160)
    requirements_hash: str = Field(min_length=1, max_length=160)
    design_artifact_hash: str = Field(min_length=1, max_length=160)
    target_facts_hash: str = Field(min_length=1, max_length=160)
    discovery_evidence_reference: str = Field(min_length=1, max_length=200)
    capability_assessment_reference: str = Field(min_length=1, max_length=200)
    unresolved_item_ids: tuple[str, ...] = ()


class EvidenceBoundHandoffCoordinator:
    """Guard artifact handoffs without interpreting missing evidence as verified facts."""

    def build_validation_plan(
        self,
        discovery_batch: DiscoveryBatchResult,
        handoff: DesignEvidenceHandoff,
        validation_adapter: VirtualValidationPathAdapter,
    ) -> VirtualValidationPlan:
        """Create a queued validation plan only when all prior evidence remains resolved and bound."""

        self._validate_handoff(discovery_batch, handoff)
        responsibility_model = MultiAgentResponsibilityModel()
        if not responsibility_model.stage_follows(
            CoordinationStage.CAPABILITY_ASSESSMENT,
            CoordinationStage.VIRTUAL_VALIDATION,
        ):
            raise RuntimeError("The multi-agent responsibility model does not permit this handoff.")
        return validation_adapter.plan(
            artifact_hash=handoff.design_artifact_hash,
            target_facts_hash=handoff.target_facts_hash,
            scope_hash=handoff.scope_hash,
        )

    @staticmethod
    def _validate_handoff(discovery_batch: DiscoveryBatchResult, handoff: DesignEvidenceHandoff) -> None:
        """Reject stale, cross-site, unresolved, or incomplete evidence before validation submission."""

        if discovery_batch.site_id != handoff.site_id:
            raise ValueError("Discovery evidence belongs to a different site.")
        if discovery_batch.scope_hash != handoff.scope_hash:
            raise ValueError("Discovery evidence is not bound to the design scope.")
        if discovery_batch.has_unresolved_results:
            raise ValueError("Discovery evidence includes unresolved targets and cannot enter validation.")
        if handoff.unresolved_item_ids:
            raise ValueError("Unresolved design or capability items cannot enter validation.")
