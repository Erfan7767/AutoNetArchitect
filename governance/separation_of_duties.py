"""Separation-of-duties controls for human governance checkpoints."""
from __future__ import annotations

from enum import Enum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .accountability_matrix import RiskClass
from .signoff_policy import CheckpointRecord, CheckpointType


class Duty(str, Enum):
    """Human duties that must remain distinguishable."""

    REVIEW = "review"
    APPROVAL = "approval"
    ACCOUNTABILITY = "accountability"
    EXECUTION = "execution_authority"


class DutyConflict(BaseModel):
    """One detected separation-of-duties conflict."""

    model_config = ConfigDict(extra="forbid")

    principal_id: str
    duties: tuple[Duty, ...]
    workflow: str
    risk_class: RiskClass
    reason: str


class SeparationEvaluation(BaseModel):
    """Explainable separation-of-duties result."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    workflow: str
    risk_class: RiskClass
    conflicts: tuple[DutyConflict, ...] = ()
    reasons: tuple[str, ...] = ()


class SeparationOfDutiesPolicy(BaseDesigner):
    """Evaluate incompatible duty combinations before execution."""

    def __init__(self) -> None:
        """Initialize explicit conflict rules."""
        super().__init__("SeparationOfDutiesPolicy")
        self.record_decision("sod_rules", "review_approval_execution_separated", "critical and high-risk paths require independent human roles")

    def evaluate(self, *, workflow: str, risk_class: RiskClass | str, checkpoints: Iterable[CheckpointRecord]) -> SeparationEvaluation:
        """Return conflicts for current checkpoints of a workflow."""
        selected_risk = RiskClass(risk_class)
        by_principal: dict[str, set[Duty]] = {}
        for checkpoint in checkpoints:
            if checkpoint.workflow != workflow or not checkpoint.is_current():
                continue
            duty = {CheckpointType.REVIEW: Duty.REVIEW, CheckpointType.APPROVAL: Duty.APPROVAL, CheckpointType.ACCOUNTABILITY: Duty.ACCOUNTABILITY, CheckpointType.EXECUTION_AUTHORITY: Duty.EXECUTION}[checkpoint.checkpoint_type]
            by_principal.setdefault(checkpoint.principal_id, set()).add(duty)
        conflicts: list[DutyConflict] = []
        for principal_id, duties in by_principal.items():
            forbidden: list[str] = []
            if Duty.REVIEW in duties and Duty.APPROVAL in duties:
                forbidden.append("reviewer cannot approve the same workflow")
            if Duty.APPROVAL in duties and Duty.EXECUTION in duties:
                forbidden.append("approver cannot execute the same workflow")
            if selected_risk in {RiskClass.HIGH, RiskClass.CRITICAL, RiskClass.EMERGENCY} and Duty.ACCOUNTABILITY in duties and Duty.EXECUTION in duties:
                forbidden.append("accountable owner cannot execute elevated-risk workflow")
            if forbidden:
                conflicts.append(DutyConflict(principal_id=principal_id, duties=tuple(sorted(duties, key=lambda item: item.value)), workflow=workflow, risk_class=selected_risk, reason="; ".join(forbidden)))
        allowed = not conflicts
        self.record_decision(f"sod_check:{workflow}", allowed, "separation-of-duties policy prevents incompatible human roles from collapsing into one identity")
        return SeparationEvaluation(allowed=allowed, workflow=workflow, risk_class=selected_risk, conflicts=tuple(conflicts), reasons=tuple(conflict.reason for conflict in conflicts))
