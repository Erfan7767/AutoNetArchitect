"""Orchestrator for explicit expert overrides."""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from designers.base_designer import BaseDesigner

from .human_decision_patch import HumanDecisionPatch, HumanDecisionPatchManager, PatchResult
from .override_audit import OverrideAudit
from .override_models import DecisionOrigin, OverrideApplication, OverrideRequest, OverrideType, RevalidationStatus
from .override_validator import OverrideValidator
from .rationale_registry import EngineeringRationale, RationaleRegistry
from .revalidation_trigger import RevalidationPlan, RevalidationTriggerEngine


class OverrideManager(BaseDesigner):
    """Apply expert interventions as append-only provenance-bearing decisions."""

    def __init__(self, *, validator: OverrideValidator | None = None, rationale_registry: RationaleRegistry | None = None, revalidation_engine: RevalidationTriggerEngine | None = None, audit: OverrideAudit | None = None) -> None:
        """Initialize override services."""
        super().__init__("OverrideManager")
        self.validator = validator or OverrideValidator()
        self.rationale_registry = rationale_registry or RationaleRegistry()
        self.revalidation_engine = revalidation_engine or RevalidationTriggerEngine()
        self.audit = audit or OverrideAudit()
        self.patch_manager = HumanDecisionPatchManager()
        self._applications: dict[str, OverrideApplication] = {}
        self._plans: dict[str, RevalidationPlan] = {}
        self.record_decision("override_manager_policy", "append_only_human_intervention", "overrides are additive interventions and cannot silently overwrite machine decisions")

    def apply(self, request: OverrideRequest, *, dependency_graph: Mapping[str, Iterable[str]] | None = None) -> OverrideApplication:
        """Validate and apply an intervention descriptor without mutating an external artifact implicitly."""
        if request.override_id in self._applications:
            raise ValueError(f"override already applied: {request.override_id}")
        validation = self.validator.validate(request)
        origin = DecisionOrigin.HUMAN_OVERRIDDEN if request.machine_decision_id else DecisionOrigin.HUMAN_ORIGINATED
        provenance = ((request.machine_decision_id,) if request.machine_decision_id else ()) + (request.override_id,)
        if validation.allowed:
            rationale_id = request.rationale_id or f"rationale:{request.override_id}"
            if request.rationale_id:
                self.rationale_registry.get(request.rationale_id)
            else:
                self.rationale_registry.register(EngineeringRationale(rationale_id=rationale_id, override_id=request.override_id, author_id=request.actor_id, author_role=request.actor_role, statement=request.reason, technical_basis=(request.impact,), evidence_ids=request.evidence_ids, requires_revalidation=validation.requires_revalidation))
            resulting_value = self._resulting_value(request)
            application = OverrideApplication(override_id=request.override_id, target_id=request.target_id, target_type=request.target_type, override_type=request.override_type, status="applied", origin=origin, machine_decision_id=request.machine_decision_id, resulting_value=resulting_value, original_value=request.original_value, provenance_chain=provenance, actor_id=request.actor_id, actor_role=request.actor_role, reason=request.reason, scope=request.scope, impact=request.impact, decided_at=request.decided_at, revalidation_status=RevalidationStatus.REQUIRED if validation.requires_revalidation else RevalidationStatus.NOT_REQUIRED, affected_artifact_ids=request.affected_artifact_ids, evidence_ids=request.evidence_ids, warnings=validation.warnings)
            if validation.requires_revalidation:
                plan = self.revalidation_engine.plan(application, dependency_graph=dependency_graph)
                self._plans[request.override_id] = plan
                application = application.model_copy(update={"revalidation_status": RevalidationStatus.SCHEDULED, "revalidation_trigger_ids": tuple(trigger.trigger_id for trigger in plan.triggers), "affected_artifact_ids": tuple(dict.fromkeys(application.affected_artifact_ids + tuple(trigger.artifact_id for trigger in plan.triggers)))})
        else:
            application = OverrideApplication(override_id=request.override_id, target_id=request.target_id, target_type=request.target_type, override_type=request.override_type, status="rejected", origin=origin, machine_decision_id=request.machine_decision_id, resulting_value=request.original_value, original_value=request.original_value, provenance_chain=provenance, actor_id=request.actor_id, actor_role=request.actor_role, reason=request.reason, scope=request.scope, impact=request.impact, decided_at=request.decided_at, revalidation_status=RevalidationStatus.BLOCKED, affected_artifact_ids=request.affected_artifact_ids, evidence_ids=request.evidence_ids, warnings=validation.warnings, rejection_reasons=validation.reasons)
        self._applications[request.override_id] = application
        self.record_decision(f"override:{request.override_id}", application.status, "expert intervention result retains original value, human identity, scope, impact, and revalidation state")
        self.audit.record(request, application)
        return application

    def apply_patch(self, request: OverrideRequest, patch: HumanDecisionPatch, current_value: Any, *, dependency_graph: Mapping[str, Iterable[str]] | None = None) -> tuple[OverrideApplication, PatchResult]:
        """Apply an explicit override plus a conflict-checked human decision patch."""
        application = self.apply(request, dependency_graph=dependency_graph)
        if application.status != "applied":
            return application, PatchResult(patch_id=patch.patch_id, target_id=patch.target_id, applied=False, resulting_value=current_value, conflict=False, reasons=application.rejection_reasons, provenance=application.provenance_chain)
        patch_result = self.patch_manager.apply(patch, current_value)
        if not patch_result.applied:
            updated = application.model_copy(update={"status": "rejected_patch_conflict", "revalidation_status": RevalidationStatus.BLOCKED, "rejection_reasons": patch_result.reasons})
            self._applications[request.override_id] = updated
            self.audit.record(request, updated)
            return updated, patch_result
        return application, patch_result

    def get(self, override_id: str) -> OverrideApplication:
        """Return an applied or rejected override result."""
        return self._applications[override_id]

    def plan(self, override_id: str) -> RevalidationPlan | None:
        """Return the revalidation plan associated with an override."""
        return self._plans.get(override_id)

    def history(self) -> tuple[OverrideApplication, ...]:
        """Return all override results in application order."""
        return tuple(self._applications.values())

    @staticmethod
    def _resulting_value(request: OverrideRequest) -> Any:
        """Compute an explicit resulting value without changing an external artifact."""
        mapping = {OverrideType.FORCE_ACCEPT: True, OverrideType.FORCE_REJECT: False, OverrideType.MODIFY_VALUE: request.proposed_value, OverrideType.REPLACE_RECOMMENDATION: request.proposed_value, OverrideType.DEFER_DECISION: None}
        if request.override_type in mapping:
            return mapping[request.override_type]
        if request.override_type in {OverrideType.NARROW_SCOPE, OverrideType.WIDEN_SCOPE_WITH_WARNING}:
            return {"target_ids": list(request.scope.target_ids), "device_ids": list(request.scope.device_ids), "site_ids": list(request.scope.site_ids), "scope_statement": request.scope.scope_statement, "warning": request.warning}
        return request.proposed_value
