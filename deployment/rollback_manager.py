"""Rollback safety management for deployment foundations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class RollbackDecision(str, Enum):
    """Rollback management decisions."""

    READY_FOR_REVIEW = "ready_for_review"
    PREVIEW_ONLY = "preview_only"
    BLOCKED_MISSING_HUMAN_DATA = "blocked_missing_human_data"
    BLOCKED_POLICY = "blocked_policy"
    BLOCKED_REMOTE_DESTRUCTIVE = "blocked_remote_destructive"


@dataclass(frozen=True)
class RollbackRequest:
    """Scoped rollback request with explicit safety confirmations."""

    request_id: str
    scope: tuple[str, ...]
    baseline_artifact_ids: tuple[str, ...]
    current_artifact_ids: tuple[str, ...]
    safety_policy_confirmations: dict[str, bool]
    validation_evidence_ids: tuple[str, ...] = ()
    remote_destructive: bool = False
    production_requested: bool = False
    human_approval: bool = False
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize rollback request."""
        return asdict(self) | {"scope": list(self.scope), "baseline_artifact_ids": list(self.baseline_artifact_ids), "current_artifact_ids": list(self.current_artifact_ids), "validation_evidence_ids": list(self.validation_evidence_ids), "evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class RollbackAssessment:
    """Review result for a rollback request."""

    request_id: str
    decision: str
    scope: tuple[str, ...]
    production_execution_allowed: bool
    safety_policies_preserved: dict[str, bool]
    required_prechecks: tuple[str, ...] = ()
    required_human_inputs: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize rollback assessment."""
        return asdict(self) | {"scope": list(self.scope), "required_prechecks": list(self.required_prechecks), "required_human_inputs": list(self.required_human_inputs), "reasons": list(self.reasons), "evidence_ids": list(self.evidence_ids)}


class RollbackManager:
    """Evaluate rollback safety without executing remote changes."""

    REQUIRED_POLICIES = ("management_access", "authentication", "audit_logging", "segmentation", "rollback_artifact_retained")

    def assess(self, request: RollbackRequest) -> RollbackAssessment:
        """Assess a rollback request and return a non-executable decision."""
        evidence = tuple(dict.fromkeys(str(item) for item in request.evidence_ids + request.validation_evidence_ids))
        policies = {key: bool(request.safety_policy_confirmations.get(key, False)) for key in self.REQUIRED_POLICIES}
        if request.remote_destructive:
            return RollbackAssessment(request.request_id, RollbackDecision.BLOCKED_REMOTE_DESTRUCTIVE.value, request.scope, False, policies, ("remote_destructive_policy",), (), ("remote-destructive rollback execution is blocked by policy",), evidence)
        missing: list[str] = []
        if not request.request_id:
            missing.append("request_id")
        if not request.scope:
            missing.append("scope")
        if not request.baseline_artifact_ids:
            missing.append("baseline_artifact_ids")
        if not request.current_artifact_ids:
            missing.append("current_artifact_ids")
        if missing:
            return RollbackAssessment(request.request_id, RollbackDecision.BLOCKED_MISSING_HUMAN_DATA.value, request.scope, False, policies, (), tuple(dict.fromkeys(missing)), ("rollback request is incomplete",), evidence)
        disabled = tuple(key for key, value in policies.items() if not value)
        if disabled:
            return RollbackAssessment(request.request_id, RollbackDecision.BLOCKED_POLICY.value, request.scope, False, policies, tuple(f"enable:{key}" for key in disabled), (), ("required rollback safety policy is not confirmed",), evidence)
        if request.production_requested and not request.human_approval:
            return RollbackAssessment(request.request_id, RollbackDecision.BLOCKED_MISSING_HUMAN_DATA.value, request.scope, False, policies, ("production_change_control",), ("human_approval",), ("production rollback request lacks explicit human approval",), evidence)
        required_inputs: list[str] = []
        reasons = ["rollback assessment does not authorize remote execution"]
        if not request.validation_evidence_ids:
            required_inputs.append("validation_evidence_ids")
            reasons.append("rollback evidence is not validated in the supplied validation path")
        decision = RollbackDecision.PREVIEW_ONLY.value if required_inputs else RollbackDecision.READY_FOR_REVIEW.value
        return RollbackAssessment(request.request_id, decision, request.scope, False, policies, ("confirm target identity", "confirm maintenance window", "confirm baseline artifact integrity", "verify management access after rollback"), tuple(required_inputs), tuple(reasons), evidence)

    def execute(self, request: RollbackRequest) -> RollbackAssessment:
        """Return a blocked assessment because V1 does not execute remote rollback."""
        assessment = self.assess(request)
        if assessment.decision == RollbackDecision.BLOCKED_REMOTE_DESTRUCTIVE.value:
            return assessment
        return RollbackAssessment(assessment.request_id, RollbackDecision.PREVIEW_ONLY.value, assessment.scope, False, assessment.safety_policies_preserved, assessment.required_prechecks, tuple(dict.fromkeys(assessment.required_human_inputs + ("external_change_control_executor",))), assessment.reasons + ("no remote rollback executor is enabled in V1",), assessment.evidence_ids)
