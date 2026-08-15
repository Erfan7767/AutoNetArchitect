"""Safety classification for deployment and rollback-risk decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Sequence


class SafetyClass(str, Enum):
    """Operational safety classes."""

    READ_ONLY = "read_only"
    NON_DISRUPTIVE = "non_disruptive"
    DISRUPTIVE = "disruptive"
    REMOTE_DESTRUCTIVE = "remote_destructive"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SafetyAssessment:
    """Safety result with rollback and production path requirements."""

    operation_id: str
    safety_class: str
    rollback_risk: str
    allowed: bool
    production_path: str
    required_approvals: tuple[str, ...] = ()
    required_prechecks: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    remote_destructive_blocked: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize safety assessment."""
        return asdict(self) | {"required_approvals": list(self.required_approvals), "required_prechecks": list(self.required_prechecks), "reasons": list(self.reasons), "evidence_ids": list(self.evidence_ids)}


class SafetyClassifier:
    """Classify operations conservatively before any connection or execution path."""

    READ_ONLY_OPERATIONS = {"discover", "verify", "show", "health_check", "collect_evidence"}
    NON_DISRUPTIVE_OPERATIONS = {"set_description", "add_metadata", "stage_candidate"}
    DISRUPTIVE_OPERATIONS = {"reload", "restart_service", "change_routing", "change_acl", "replace_config", "rollback"}

    def classify(
        self,
        operation_id: str,
        operation: str,
        *,
        remote: bool = False,
        destructive: bool = False,
        affects_management: bool = False,
        rollback_artifact_available: bool = False,
        production_requested: bool = False,
        human_change_approval: bool = False,
        evidence_ids: Sequence[str] = (),
    ) -> SafetyAssessment:
        """Return an explicit classification and gate without executing anything."""
        normalized = str(operation).strip().lower()
        reasons: list[str] = []
        approvals: list[str] = []
        prechecks: list[str] = []
        if remote and destructive:
            return SafetyAssessment(operation_id, SafetyClass.REMOTE_DESTRUCTIVE.value, "critical", False, "blocked", ("remote_destructive_policy",), ("human_scope_confirmation",), ("remote-destructive operations are blocked by policy",), tuple(dict.fromkeys(str(item) for item in evidence_ids)))
        if normalized in self.READ_ONLY_OPERATIONS and not destructive:
            safety_class = SafetyClass.READ_ONLY.value
            risk = "low"
        elif normalized in self.NON_DISRUPTIVE_OPERATIONS and not destructive:
            safety_class = SafetyClass.NON_DISRUPTIVE.value
            risk = "medium"
            prechecks.append("confirm target identity")
        elif normalized in self.DISRUPTIVE_OPERATIONS or destructive:
            safety_class = SafetyClass.DISRUPTIVE.value
            risk = "high"
            approvals.append("human_change_approval")
            prechecks.extend(("confirm target identity", "validate rollback artifact", "validate maintenance window"))
            if not rollback_artifact_available:
                reasons.append("rollback artifact is missing")
        else:
            return SafetyAssessment(operation_id, SafetyClass.UNKNOWN.value, "unknown", False, "blocked", ("human_operation_classification",), ("target_identity",), ("operation is not in the validated V1 vocabulary",), tuple(dict.fromkeys(str(item) for item in evidence_ids)))
        if affects_management:
            approvals.append("management_access_review")
            prechecks.append("verify alternate management path")
            reasons.append("operation affects management access")
        if production_requested:
            approvals.append("production_change_control")
            if not human_change_approval:
                reasons.append("production request lacks explicit human change approval")
        allowed = not reasons and (not production_requested or human_change_approval)
        production_path = "allowed_with_change_control" if allowed and production_requested else "review_only" if allowed else "blocked"
        return SafetyAssessment(operation_id, safety_class, risk, allowed, production_path, tuple(dict.fromkeys(approvals)), tuple(dict.fromkeys(prechecks)), tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(str(item) for item in evidence_ids)))
