"""Evidence-bound local virtual validation workflow for the Windows shell."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from site_agent.discovery_coordination import DiscoveryBatchResult
from site_agent.evidence_handoff import DesignEvidenceHandoff, EvidenceBoundHandoffCoordinator
from site_agent.models import VirtualTestResult
from site_agent.virtual_adapters import VirtualValidationPathAdapter, VirtualValidationPlan
from site_agent.virtual_validation import VirtualTestAdapter, VirtualValidationCoordinator

from .workspace import WindowsWorkspace


class LocalVirtualValidationRecord(BaseModel):
    """Saved local validation evidence that never grants production execution authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    plan: VirtualValidationPlan
    result: VirtualTestResult
    production_execution_permitted: bool = False


class LocalVirtualValidationController:
    """Bind a local virtual test to approved scope, resolved discovery, and exact capability evidence."""

    def __init__(self, workspace: WindowsWorkspace, result_adapter: VirtualTestAdapter | None = None) -> None:
        """Create a controller with an injected validation adapter; it never contacts production devices."""

        self._workspace = workspace
        self._result_adapter = result_adapter

    def validate(
        self,
        discovery_batch: DiscoveryBatchResult,
        handoff: DesignEvidenceHandoff,
        validation_adapter: VirtualValidationPathAdapter,
    ) -> LocalVirtualValidationRecord:
        """Run and persist a strictly hash-bound local validation result without authorizing production execution."""

        if self._result_adapter is None:
            raise RuntimeError("A human-provided external lab adapter is required to produce local virtual-test evidence.")
        plan = self.prepare(discovery_batch, handoff, validation_adapter)
        result = VirtualValidationCoordinator(self._result_adapter).validate(
            artifact_hash=plan.artifact_hash,
            target_facts_hash=plan.target_facts_hash,
            scope_hash=plan.scope_hash,
        )
        if result.adapter_kind != plan.adapter_kind or result.fidelity_label != plan.fidelity_label.value:
            raise ValueError("Virtual-test evidence adapter or fidelity does not match the approved local validation plan.")
        persisted = self._workspace.save_virtual_test_result(result)
        return LocalVirtualValidationRecord(plan=plan, result=persisted)

    def prepare(
        self,
        discovery_batch: DiscoveryBatchResult,
        handoff: DesignEvidenceHandoff,
        validation_adapter: VirtualValidationPathAdapter,
    ) -> VirtualValidationPlan:
        """Prepare a hash-bound local validation plan; a real external lab adapter remains required to produce a result."""

        scope = self._workspace.load_scope()
        if scope is None:
            raise PermissionError("Local virtual validation is blocked until a human-approved local scope is saved.")
        if scope.site_id != handoff.site_id:
            raise ValueError("The local approved scope belongs to a different site than the validation handoff.")
        if scope.evidence_hash() != handoff.scope_hash:
            raise ValueError("The validation handoff scope hash does not match the locally approved scope.")
        authorization = self._workspace.load_laboratory_authorization()
        if authorization is None:
            raise PermissionError("Local virtual validation is blocked until a written human laboratory authorization is saved.")
        if not authorization.active_for(scope.evidence_hash()):
            raise PermissionError("Written laboratory authorization is expired, outside the approved scope, or not yet active.")

        plan = EvidenceBoundHandoffCoordinator().build_validation_plan(discovery_batch, handoff, validation_adapter)
        if plan.production_change_authority:
            raise RuntimeError("Local virtual validation plans must never grant production change authority.")
        return plan
