"""Human authority grants and execution eligibility."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .accountability_matrix import RiskClass
from .signoff_policy import CheckpointType


class AuthorityType(str, Enum):
    """Types of human authority kept separate by policy."""

    REVIEWER = "reviewer"
    APPROVER = "approver"
    ACCOUNTABLE_OWNER = "accountable_owner"
    EXECUTOR = "executor"
    ESCALATION = "escalation"


class AuthorityGrant(BaseModel):
    """Time-bounded authority grant for one principal."""

    model_config = ConfigDict(extra="forbid")

    grant_id: str = Field(min_length=1)
    principal_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    authority_type: AuthorityType
    workflows: tuple[str, ...] = ()
    maximum_risk: RiskClass = RiskClass.MEDIUM
    reference: str = ""
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    active: bool = True

    def is_current(self, *, workflow: str, risk_class: RiskClass, now: datetime | None = None) -> bool:
        """Return whether the grant covers a workflow and risk at a point in time."""
        if not self.active or (self.workflows and workflow not in self.workflows):
            return False
        selected_now = now or datetime.now(timezone.utc)
        if self.expires_at is not None:
            expiry = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
            if expiry <= selected_now:
                return False
        order = {RiskClass.LOW: 1, RiskClass.MEDIUM: 2, RiskClass.HIGH: 3, RiskClass.CRITICAL: 4, RiskClass.EMERGENCY: 5}
        return order[risk_class] <= order[self.maximum_risk]


class AuthorityDecision(BaseModel):
    """Explainable result of an authority lookup."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    principal_id: str
    workflow: str
    authority_type: AuthorityType
    required_role: str
    matched_grant_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


class AuthorityModel(BaseDesigner):
    """Manage explicit human authority grants without conflating them with approval."""

    def __init__(self) -> None:
        """Initialize an empty authority registry."""
        super().__init__("AuthorityModel")
        self._grants: dict[str, AuthorityGrant] = {}
        self.record_decision("authority_default", "deny_without_grant", "execution authority is never inferred from a role name or an approval alone")

    def grant(self, grant: AuthorityGrant) -> AuthorityGrant:
        """Register a grant after validating its scope."""
        if not grant.workflows:
            self.record_assumption(f"grant_scope:{grant.grant_id}", "all_workflows", "empty workflow scope is interpreted as explicit all-workflow authority only when a human policy owner grants it")
        self._grants[grant.grant_id] = grant
        self.record_decision(f"grant:{grant.grant_id}", grant.authority_type.value, "authority grant was explicitly registered with principal, role, risk ceiling, and expiry")
        return grant

    def revoke(self, grant_id: str, reason: str) -> AuthorityGrant:
        """Deactivate a grant with a mandatory reason."""
        if not reason.strip():
            raise ValueError("authority revocation reason is mandatory")
        current = self._grants[grant_id]
        updated = current.model_copy(update={"active": False})
        self._grants[grant_id] = updated
        self.record_decision(f"revoke:{grant_id}", "revoked", reason)
        return updated

    def check(self, *, principal_id: str, workflow: str, risk_class: RiskClass | str, authority_type: AuthorityType | str, required_role: str, now: datetime | None = None) -> AuthorityDecision:
        """Check whether a principal has current authority for a workflow."""
        selected_risk = RiskClass(risk_class)
        selected_type = AuthorityType(authority_type)
        matched = tuple(grant.grant_id for grant in self._grants.values() if grant.principal_id == principal_id and grant.authority_type == selected_type and grant.role == required_role and grant.is_current(workflow=workflow, risk_class=selected_risk, now=now))
        allowed = bool(matched)
        reasons = () if allowed else (f"principal lacks current {selected_type.value} authority for role {required_role}",)
        self.record_decision(f"authority_check:{principal_id}:{workflow}:{selected_type.value}", allowed, "authority is checked against an explicit active grant")
        return AuthorityDecision(allowed=allowed, principal_id=principal_id, workflow=workflow, authority_type=selected_type, required_role=required_role, matched_grant_ids=matched, reasons=reasons)

    def grants(self) -> tuple[AuthorityGrant, ...]:
        """Return all grants in stable registration order."""
        return tuple(self._grants.values())
