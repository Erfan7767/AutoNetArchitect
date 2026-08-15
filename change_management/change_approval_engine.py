"""Approval policy engine for normal, standard, emergency, and sector changes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Sequence

from designers.base_designer import DecisionRecord

from .change_models import Approval, ApprovalDecision, ChangeRequest, ChangeType, RiskLevel


@dataclass(frozen=True)
class ApprovalRequirements:
    """Required approval roles and policy rationale."""

    required_roles: tuple[str, ...]
    rationale: tuple[str, ...]
    pre_approved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize requirements."""
        return asdict(self) | {"required_roles": list(self.required_roles), "rationale": list(self.rationale)}


@dataclass(frozen=True)
class ApprovalEvaluation:
    """Current approval state for a request."""

    state: str
    required_roles: tuple[str, ...]
    approved_roles: tuple[str, ...]
    pending_roles: tuple[str, ...]
    rejected_roles: tuple[str, ...]
    conditions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize approval evaluation."""
        return asdict(self) | {"required_roles": list(self.required_roles), "approved_roles": list(self.approved_roles), "pending_roles": list(self.pending_roles), "rejected_roles": list(self.rejected_roles), "conditions": list(self.conditions)}


class ChangeApprovalEngine:
    """Apply all-required approval policy with explicit sector overrides."""

    def requirements(self, request: ChangeRequest, *, sector: str = "general", clinical_sensitive: bool = False) -> ApprovalRequirements:
        """Determine required roles from type and risk level."""
        rationale: list[str] = []
        if request.change_type == ChangeType.STANDARD.value:
            roles: list[str] = []
            pre_approved = True
            rationale.append("standard changes rely on a current catalog pre-approval")
        elif request.change_type == ChangeType.EMERGENCY.value:
            roles = ["on_call_manager"]
            pre_approved = False
            rationale.append("emergency changes require on-call approval and post-implementation review")
        else:
            roles = ["technical_reviewer", "change_manager"]
            pre_approved = False
            rationale.append("normal changes require technical reviewer and change manager")
            if request.risk_assessment.risk_level in {RiskLevel.HIGH.value, RiskLevel.CRITICAL.value}:
                roles.append("service_owner")
                rationale.append("high or critical risk requires service owner approval")
            if request.risk_assessment.risk_level == RiskLevel.CRITICAL.value:
                roles.append("cto_or_it_director")
                rationale.append("critical risk requires executive or IT director approval")
        normalized_sector = sector.lower()
        if normalized_sector == "banking":
            roles.append("security_reviewer")
            rationale.append("banking domain adds security review")
        if normalized_sector in {"hospital", "hospital_clinical", "clinical"} and clinical_sensitive:
            roles.append("clinical_impact_reviewer")
            rationale.append("clinical-sensitive hospital change adds clinical impact review")
        return ApprovalRequirements(tuple(dict.fromkeys(roles)), tuple(rationale), pre_approved)

    def record(self, request: ChangeRequest, approval: Approval) -> ApprovalEvaluation:
        """Record one approval and return current aggregate state."""
        if approval.decision not in {item.value for item in ApprovalDecision}:
            raise ValueError("unsupported approval decision")
        if approval.decided_at is None:
            approval = Approval(approval.approver_role, approval.approver_name, approval.decision, approval.decision_reason, datetime.now(timezone.utc), approval.conditions)
        request.approvals.append(approval)
        evaluation = self.evaluate(request, tuple(item.approver_role for item in request.approvals))
        request.decision_records.append(DecisionRecord("ChangeApprovalEngine", f"{request.change_id}:approval:{len(request.approvals)}", approval.decision, ["approved", "rejected", "deferred"], {"rejected": "any rejection blocks the change", "deferred": "requires more information"}))
        return evaluation

    def evaluate(self, request: ChangeRequest, required_roles: Sequence[str]) -> ApprovalEvaluation:
        """Evaluate all required approver roles from recorded approvals."""
        roles = tuple(dict.fromkeys(str(role) for role in required_roles))
        decisions = {approval.approver_role: approval for approval in request.approvals}
        rejected = tuple(sorted(role for role in roles if decisions.get(role) and decisions[role].decision == ApprovalDecision.REJECTED.value))
        approved = tuple(sorted(role for role in roles if decisions.get(role) and decisions[role].decision in {ApprovalDecision.APPROVED.value, ApprovalDecision.APPROVED_WITH_CONDITIONS.value}))
        pending = tuple(sorted(role for role in roles if role not in decisions or decisions[role].decision in {ApprovalDecision.PENDING.value, ApprovalDecision.DEFERRED.value}))
        conditions = tuple(condition for role in approved for condition in decisions[role].conditions if decisions[role].decision == ApprovalDecision.APPROVED_WITH_CONDITIONS.value)
        if rejected:
            state = "rejected"
        elif not pending and len(approved) == len(roles):
            state = "approved_with_conditions" if conditions else "approved"
        else:
            state = "pending"
        return ApprovalEvaluation(state, roles, approved, pending, rejected, conditions)

    @staticmethod
    def can_execute(evaluation: ApprovalEvaluation) -> bool:
        """Return whether approval state permits scheduling or execution."""
        return evaluation.state in {"approved", "approved_with_conditions"}
