"""Time-bounded exception and waiver governance."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from audit.audit_trail import AuditTrail
from designers.base_designer import BaseDesigner

from .accountability_matrix import RiskClass


class WaiverStatus(str, Enum):
    """Lifecycle states for an exception waiver."""

    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class WaiverRequest(BaseModel):
    """Human-owned request to temporarily deviate from a governance control."""

    model_config = ConfigDict(extra="forbid")

    waiver_id: str = Field(min_length=1)
    workflow: str = Field(min_length=1)
    boundary_or_policy: str = Field(min_length=1)
    risk_class: RiskClass
    requester_id: str = Field(min_length=1)
    accountable_owner_id: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    impact_if_granted: str = Field(min_length=1)
    compensating_controls: tuple[str, ...] = ()
    validation_plan: tuple[str, ...] = ()
    reviewer_references: tuple[str, ...] = ()
    approver_reference: str = ""
    evidence_ids: tuple[str, ...] = ()
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime

    def is_time_bounded(self) -> bool:
        """Return whether expiry is later than request time."""
        start = self.requested_at if self.requested_at.tzinfo else self.requested_at.replace(tzinfo=timezone.utc)
        expiry = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return expiry > start


class WaiverAssessment(BaseModel):
    """Explainable waiver state and enforcement result."""

    model_config = ConfigDict(extra="forbid")

    waiver_id: str
    status: WaiverStatus
    enforceable: bool
    reasons: tuple[str, ...] = ()
    required_actions: tuple[str, ...] = ()
    expires_at: datetime
    evidence_ids: tuple[str, ...] = ()


class ExceptionWaiverRegistry(BaseDesigner):
    """Register and evaluate waivers without turning them into permanent policy."""

    def __init__(self, *, audit_trail: AuditTrail | None = None) -> None:
        """Initialize an empty waiver registry."""
        super().__init__("ExceptionWaiverRegistry")
        self.audit_trail = audit_trail
        self._requests: dict[str, WaiverRequest] = {}
        self._statuses: dict[str, WaiverStatus] = {}
        self.record_decision("waiver_default", "deny_without_expiry_and_approval", "every exception must be time-bounded, justified, reviewed, and approved")

    def submit(self, request: WaiverRequest) -> WaiverAssessment:
        """Submit a waiver request and assess whether it may proceed to approval."""
        reasons: list[str] = []
        required: list[str] = []
        if not request.is_time_bounded():
            reasons.append("waiver expiry must be later than request time")
        if not request.compensating_controls:
            reasons.append("at least one compensating control is required")
            required.append("compensating_controls")
        if not request.validation_plan:
            reasons.append("waiver validation plan is required")
            required.append("validation_plan")
        if not request.reviewer_references:
            reasons.append("independent reviewer reference is required")
            required.append("reviewer_references")
        if request.approver_reference and not request.approver_reference.startswith("approval://"):
            reasons.append("approver reference must use approval:// scheme")
        status = WaiverStatus.REQUESTED if not reasons else WaiverStatus.REJECTED
        self._requests[request.waiver_id] = request
        self._statuses[request.waiver_id] = status
        assessment = WaiverAssessment(waiver_id=request.waiver_id, status=status, enforceable=False, reasons=tuple(dict.fromkeys(reasons)), required_actions=tuple(dict.fromkeys(required + ["obtain_approval_reference", "review_expiry_before_use"])), expires_at=request.expires_at, evidence_ids=request.evidence_ids)
        self.record_decision(f"waiver_submit:{request.waiver_id}", status.value, "waiver is not enforceable until an explicit approval is recorded")
        if not request.compensating_controls:
            self.record_assumption(f"waiver_controls:{request.waiver_id}", "missing", "no compensating control was supplied")
        self._audit(request, assessment)
        return assessment

    def approve(self, waiver_id: str, *, approver_reference: str, rationale: str) -> WaiverAssessment:
        """Approve a requested waiver with a mandatory approval reference and rationale."""
        if not approver_reference.startswith("approval://"):
            raise ValueError("waiver approval reference must use approval:// scheme")
        if not rationale.strip():
            raise ValueError("waiver approval rationale is mandatory")
        request = self._requests[waiver_id]
        now = datetime.now(timezone.utc)
        if request.expires_at <= now:
            self._statuses[waiver_id] = WaiverStatus.EXPIRED
            return self.assessment(waiver_id)
        self._statuses[waiver_id] = WaiverStatus.APPROVED
        assessment = WaiverAssessment(waiver_id=waiver_id, status=WaiverStatus.APPROVED, enforceable=True, reasons=(rationale,), required_actions=("monitor_compensating_controls", "close_or_revalidate_before_expiry"), expires_at=request.expires_at, evidence_ids=request.evidence_ids)
        self.record_decision(f"waiver_approve:{waiver_id}", "approved", "waiver approval is explicit, referenced, and time-bounded")
        self._audit(request, assessment)
        return assessment

    def revoke(self, waiver_id: str, reason: str) -> WaiverAssessment:
        """Revoke a waiver before expiry."""
        if not reason.strip():
            raise ValueError("waiver revocation reason is mandatory")
        self._statuses[waiver_id] = WaiverStatus.REVOKED
        assessment = self.assessment(waiver_id)
        self.record_decision(f"waiver_revoke:{waiver_id}", "revoked", reason)
        self._audit(self._requests[waiver_id], assessment)
        return assessment

    def assessment(self, waiver_id: str, *, now: datetime | None = None) -> WaiverAssessment:
        """Return current enforceability, converting approved expired waivers to EXPIRED."""
        request = self._requests[waiver_id]
        selected_now = now or datetime.now(timezone.utc)
        status = self._statuses[waiver_id]
        if status == WaiverStatus.APPROVED and request.expires_at <= selected_now:
            status = WaiverStatus.EXPIRED
            self._statuses[waiver_id] = status
        enforceable = status == WaiverStatus.APPROVED and request.expires_at > selected_now
        return WaiverAssessment(waiver_id=waiver_id, status=status, enforceable=enforceable, reasons=() if enforceable else ("waiver is not currently enforceable",), required_actions=("human_revalidation",) if status in {WaiverStatus.EXPIRED, WaiverStatus.REVOKED} else (), expires_at=request.expires_at, evidence_ids=request.evidence_ids)

    def active(self, *, now: datetime | None = None) -> tuple[WaiverAssessment, ...]:
        """Return currently enforceable waivers."""
        return tuple(self.assessment(waiver_id, now=now) for waiver_id in self._requests if self.assessment(waiver_id, now=now).enforceable)

    def _audit(self, request: WaiverRequest, assessment: WaiverAssessment) -> None:
        """Record waiver metadata without any secret values."""
        if self.audit_trail is None:
            return
        self.audit_trail.record("governance.waiver", request.requester_id, {"waiver_id": request.waiver_id, "workflow": request.workflow, "boundary_or_policy": request.boundary_or_policy, "risk_class": request.risk_class.value, "status": assessment.status.value, "enforceable": assessment.enforceable, "expires_at": request.expires_at.isoformat(), "evidence_ids": list(request.evidence_ids)}, outcome=assessment.status.value)
