"""Build reviewable implementation plans from configuration artifacts."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Callable, Sequence

from deployment.safety_classifier import SafetyClassifier
from designers.base_designer import Assumption, DecisionRecord

from .change_models import ChangeRequest, ImplementationPlan, ImplementationStep


class ChangePlanBuilder:
    """Construct ordered implementation steps without fabricating device commands."""

    def build(
        self,
        request: ChangeRequest,
        *,
        validator: Callable[[str, Sequence[str]], bool] | None = None,
        safety_classifier: SafetyClassifier | None = None,
        step_duration: timedelta | None = None,
        parallel_ok: bool = False,
        human_checkpoints: bool = True,
    ) -> ImplementationPlan:
        """Build the plan and attach decision/assumption records to the request."""
        classifier = safety_classifier or SafetyClassifier()
        steps: list[ImplementationStep] = []
        assumptions: list[Assumption] = []
        validator_evidence: list[str] = []
        for index, change in enumerate(request.config_changes, start=1):
            if validator is not None and not validator(change.device_id, change.commands_to_apply):
                raise ValueError(f"config validator rejected change for {change.device_id}")
            if validator is None:
                assumptions.append(Assumption(f"validator:{change.device_id}:{index}", "not_configured", "commands cannot be considered validated without a supplied validator", True))
            if not change.commands_to_apply:
                assumptions.append(Assumption(f"commands:{change.device_id}:{index}", "not_supplied", "no exact commands are fabricated by the change planner", True))
            safety = classifier.classify(f"{request.change_id}:step:{index}", "replace_config", rollback_artifact_available=bool(change.commands_to_rollback), production_requested=True, human_change_approval=False, evidence_ids=change.validator_evidence_ids)
            if safety.safety_class == "remote_destructive" or "rollback artifact is missing" in safety.reasons:
                assumptions.append(Assumption(f"safety:{change.device_id}:{index}", "review_required", "step safety requires rollback evidence and change approval", True))
            duration = step_duration if step_duration is not None else timedelta(0)
            if step_duration is None:
                assumptions.append(Assumption(f"duration:{change.device_id}:{index}", "not_supplied", "duration is not estimated from an invented device behavior", True))
            steps.append(ImplementationStep(index, f"review and apply {change.change_section} on {change.device_name or change.device_id}", change.device_id, change.commands_to_apply, "human-confirmed expected result", "human-supplied verification command", "human-supplied expected output", duration, change.commands_to_rollback, False, human_checkpoints, ("identity confirmed", "precheck healthy", "post-step verification acceptable",)))
            validator_evidence.extend(change.validator_evidence_ids)
        total_duration = sum((step.estimated_duration for step in steps), timedelta(0))
        plan = ImplementationPlan(tuple(steps), total_duration, True, request.impact_assessment.impact_class, "parallel" if parallel_ok and len({step.device for step in steps}) == len(steps) else "sequential", ("backup verified", "approval conditions satisfied", "maintenance window active"), tuple(dict.fromkeys(validator_evidence)))
        request.implementation_plan = plan
        request.assumptions.extend(assumptions)
        request.decision_records.append(DecisionRecord("ChangePlanBuilder", f"{request.change_id}:implementation_plan", plan.parallel_vs_sequential, ["parallel", "sequential"], {"parallel": "not selected unless explicit independence is supplied", "sequential": "selected by default for safety"}))
        return plan
