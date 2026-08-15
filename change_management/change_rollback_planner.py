"""Build explicit rollback plans for change requests."""

from __future__ import annotations

from datetime import timedelta
from typing import Sequence

from designers.base_designer import Assumption, DecisionRecord

from .change_models import ChangeRequest, RollbackPlan, RollbackStep, RollbackStrategy


class ChangeRollbackPlanner:
    """Create safety-preserving rollback plans without executing them."""

    def build(
        self,
        request: ChangeRequest,
        *,
        strategy: str = RollbackStrategy.FULL_ROLLBACK.value,
        trigger_criteria: Sequence[str] = (),
        backup_evidence_ids: Sequence[str] = (),
        point_of_no_return: int | None = None,
        partial_rollback_possible: bool = True,
        step_duration: timedelta | None = None,
    ) -> RollbackPlan:
        """Build a rollback plan from implementation-step rollback commands."""
        if strategy not in {item.value for item in RollbackStrategy}:
            raise ValueError("unsupported rollback strategy")
        assumptions: list[Assumption] = []
        steps: list[RollbackStep] = []
        duration = step_duration if step_duration is not None else timedelta(0)
        for implementation_step in reversed(request.implementation_plan.steps):
            if not implementation_step.rollback_commands:
                assumptions.append(Assumption(f"rollback_commands:{implementation_step.step_number}", "not_supplied", "rollback commands are not invented when the generator did not provide them", True))
            if step_duration is None:
                assumptions.append(Assumption(f"rollback_duration:{implementation_step.step_number}", "not_supplied", "rollback duration requires human or validated operational evidence", True))
            steps.append(RollbackStep(implementation_step.step_number, f"rollback {implementation_step.description}", implementation_step.device, implementation_step.rollback_commands, "human-confirmed baseline restored", "human-supplied rollback verification", "human-supplied expected baseline output", duration))
        if not backup_evidence_ids:
            assumptions.append(Assumption("backup_evidence", "missing", "a current valid backup must be verified before a production change", True))
        plan = RollbackPlan(strategy, tuple(steps), sum((step.estimated_duration for step in steps), timedelta(0)), tuple(dict.fromkeys(str(item) for item in trigger_criteria)) or ("explicit human rollback decision", "verification failure against rollback criteria", "maximum change duration exceeded"), point_of_no_return, partial_rollback_possible, True, tuple(dict.fromkeys(str(item) for item in backup_evidence_ids)), ("management_access", "authentication", "audit_logging", "segmentation"))
        request.rollback_plan = plan
        request.assumptions.extend(assumptions)
        request.decision_records.append(DecisionRecord("ChangeRollbackPlanner", f"{request.change_id}:rollback_plan", strategy, [item.value for item in RollbackStrategy], {item.value: "not selected" for item in RollbackStrategy if item.value != strategy}))
        return plan
