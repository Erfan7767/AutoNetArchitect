"""Emergency change policy with narrow authority and retrospective governance."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from audit.audit_trail import AuditTrail
from designers.base_designer import BaseDesigner


class EmergencyChangeRequest(BaseModel):
    """Human-declared emergency change request."""

    model_config = ConfigDict(extra="forbid")

    emergency_id: str = Field(min_length=1)
    workflow: str = "emergency_change"
    decision_class: str = "emergency_change"
    requester_id: str = Field(min_length=1)
    justification: str = Field(min_length=1)
    affected_scope: tuple[str, ...] = ()
    impact_summary: str = Field(min_length=1)
    on_call_approval_reference: str = ""
    override_reference: str = ""
    backup_reference: str = ""
    rollback_reference: str = ""
    evidence_ids: tuple[str, ...] = ()
    declared_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    maximum_execution_minutes: int = Field(default=60, ge=1, le=240)


class EmergencyAssessment(BaseModel):
    """Decision and follow-up obligations for an emergency change."""

    model_config = ConfigDict(extra="forbid")

    emergency_id: str
    allowed: bool
    state: str
    reasons: tuple[str, ...] = ()
    required_actions: tuple[str, ...] = ()
    override_used: bool = False
    audit_required: bool = True
    post_implementation_review_due: datetime | None = None
    governance_review_due: datetime | None = None
    evidence_ids: tuple[str, ...] = ()


class EmergencyChangePolicy(BaseDesigner):
    """Enforce bounded emergency overrides without making them a normal path."""

    def __init__(self, *, audit_trail: AuditTrail | None = None) -> None:
        """Initialize policy with optional append-only audit integration."""
        super().__init__("EmergencyChangePolicy")
        self.audit_trail = audit_trail
        self.record_decision("emergency_change_default", "deny_without_on_call_approval_and_recovery_evidence", "emergency execution must remain narrow, recoverable, and auditable")

    def assess(self, request: EmergencyChangeRequest, *, now: datetime | None = None) -> EmergencyAssessment:
        """Assess emergency eligibility and compute retrospective governance deadlines."""
        selected_now = now or datetime.now(timezone.utc)
        reasons: list[str] = []
        required: list[str] = []
        if not request.justification.strip():
            reasons.append("emergency justification is mandatory")
        if not request.affected_scope:
            reasons.append("emergency scope must be explicitly bounded")
        if not request.on_call_approval_reference.startswith("approval://"):
            reasons.append("on-call approval reference must use approval:// scheme")
            required.append("on_call_approval_reference")
        if not request.backup_reference:
            reasons.append("emergency path requires a backup reference")
            required.append("backup_reference")
        if not request.rollback_reference:
            reasons.append("emergency path requires a rollback reference")
            required.append("rollback_reference")
        override_used = bool(request.override_reference)
        if override_used and not request.override_reference.startswith("approval://"):
            reasons.append("emergency override reference must use approval:// scheme")
            required.append("override_reference")
        allowed = not reasons
        review_due = selected_now + timedelta(hours=24)
        governance_due = selected_now + timedelta(hours=72)
        state = "allowed_with_retrospective_review" if allowed else "blocked_pending_emergency_governance"
        assessment = EmergencyAssessment(emergency_id=request.emergency_id, allowed=allowed, state=state, reasons=tuple(dict.fromkeys(reasons)), required_actions=tuple(dict.fromkeys(required + ["record_post_implementation_review", "record_governance_review_within_72_hours"])), override_used=override_used, post_implementation_review_due=review_due, governance_review_due=governance_due, evidence_ids=request.evidence_ids)
        self.record_decision(f"emergency:{request.emergency_id}", state, "emergency assessment requires explicit scope, on-call approval, recovery references, and retrospective review")
        if not request.backup_reference:
            self.record_assumption(f"emergency_backup:{request.emergency_id}", "missing", "emergency cannot be treated as recoverable without a backup reference")
        self._audit(request, assessment)
        return assessment

    def _audit(self, request: EmergencyChangeRequest, assessment: EmergencyAssessment) -> None:
        """Write audit-safe emergency metadata when an audit trail is configured."""
        if self.audit_trail is None:
            return
        self.audit_trail.record("governance.emergency_change", request.requester_id, {"emergency_id": request.emergency_id, "workflow": request.workflow, "affected_scope": list(request.affected_scope), "override_used": assessment.override_used, "allowed": assessment.allowed, "state": assessment.state, "evidence_ids": list(request.evidence_ids), "post_implementation_review_due": assessment.post_implementation_review_due.isoformat() if assessment.post_implementation_review_due else None, "governance_review_due": assessment.governance_review_due.isoformat() if assessment.governance_review_due else None}, outcome=assessment.state)
