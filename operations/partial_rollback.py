"""Scoped partial rollback planning with preserved safety controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Sequence


class RollbackStatus(str, Enum):
    """Planning outcomes for scoped rollback."""

    READY_FOR_REVIEW = "ready_for_review"
    PREVIEW_ONLY = "preview_only"
    BLOCKED_MISSING_HUMAN_DATA = "blocked_missing_human_data"
    BLOCKED_POLICY_VIOLATION = "blocked_policy_violation"


@dataclass(frozen=True)
class RollbackStep:
    """One ordered rollback planning step."""

    step_id: str
    title: str
    scope: tuple[str, ...]
    actions: tuple[str, ...]
    prerequisites: tuple[str, ...]
    safety_checks: tuple[str, ...]
    verification_checks: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the step."""
        return asdict(self) | {"scope": list(self.scope), "actions": list(self.actions), "prerequisites": list(self.prerequisites), "safety_checks": list(self.safety_checks), "verification_checks": list(self.verification_checks)}


@dataclass(frozen=True)
class RollbackPlan:
    """Non-executable partial rollback plan with scope and policy lineage."""

    plan_id: str
    status: str
    scope: tuple[str, ...]
    production_execution_allowed: bool
    human_review_required: bool
    safety_policies_preserved: dict[str, bool]
    protected_controls: tuple[str, ...]
    steps: tuple[RollbackStep, ...]
    required_human_inputs: tuple[str, ...]
    risks: tuple[str, ...]
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the rollback plan."""
        return {
            "plan_id": self.plan_id,
            "status": self.status,
            "scope": list(self.scope),
            "production_execution_allowed": self.production_execution_allowed,
            "human_review_required": self.human_review_required,
            "safety_policies_preserved": dict(self.safety_policies_preserved),
            "protected_controls": list(self.protected_controls),
            "steps": [step.to_dict() for step in self.steps],
            "required_human_inputs": list(self.required_human_inputs),
            "risks": list(self.risks),
            "evidence_ids": list(self.evidence_ids),
        }


class PartialRollbackPlanner:
    """Build a rollback plan for an explicitly bounded subset of changed assets.

    The planner preserves management, authentication, audit, logging, and
    segmentation controls by policy. It never emits an executable command and
    cannot authorize a production change.
    """

    REQUIRED_POLICIES = (
        "preserve_management_access",
        "preserve_authentication",
        "preserve_audit_logging",
        "preserve_segmentation",
        "retain_rollback_artifacts",
        "require_human_change_approval",
    )

    def plan(
        self,
        changed_scope: Sequence[str] | None,
        rollback_scope: Sequence[str] | None,
        baseline_configs: Mapping[str, Any] | None,
        current_configs: Mapping[str, Any] | None,
        *,
        safety_policies: Mapping[str, bool] | None = None,
        protected_controls: Sequence[str] = ("management_access", "authentication", "audit_logging", "segmentation"),
        evidence_ids: Sequence[str] = (),
        validation_evidence_ids: Sequence[str] = (),
        approved_change_window: str | None = None,
    ) -> RollbackPlan:
        """Create a scoped rollback plan from explicit baseline/current artifacts."""
        changed = tuple(dict.fromkeys(str(item) for item in (changed_scope or ()) if str(item)))
        scope = tuple(dict.fromkeys(str(item) for item in (rollback_scope or ()) if str(item)))
        policies = {key: True for key in self.REQUIRED_POLICIES}
        policies.update({str(key): bool(value) for key, value in (safety_policies or {}).items()})
        controls = tuple(dict.fromkeys(str(item) for item in protected_controls if str(item)))
        risks = ["V1 rollback is a reviewed plan and not a production execution authorization"]
        required: list[str] = []
        if not changed:
            required.append("changed_scope")
        if not scope:
            required.append("rollback_scope")
        if not baseline_configs:
            required.append("baseline_configs")
        if not current_configs:
            required.append("current_configs")
        if required:
            return self._blocked(RollbackStatus.BLOCKED_MISSING_HUMAN_DATA.value, scope, policies, controls, tuple(required), risks, evidence_ids, "rollback inputs are incomplete")
        outside = tuple(item for item in scope if item not in changed)
        if outside:
            risks.append("rollback scope contains assets outside the declared changed scope")
            return self._blocked(RollbackStatus.BLOCKED_POLICY_VIOLATION.value, scope, policies, controls, (f"remove_out_of_scope_asset:{item}" for item in outside), risks, evidence_ids, "partial rollback scope is not a subset of changed scope")
        missing_baseline = tuple(item for item in scope if item not in baseline_configs)
        missing_current = tuple(item for item in scope if item not in current_configs)
        if missing_baseline or missing_current:
            required.extend(f"baseline_config:{item}" for item in missing_baseline)
            required.extend(f"current_config:{item}" for item in missing_current)
            return self._blocked(RollbackStatus.BLOCKED_MISSING_HUMAN_DATA.value, scope, policies, controls, tuple(required), risks, evidence_ids, "baseline or current configuration is missing for rollback scope")
        disabled = tuple(key for key in self.REQUIRED_POLICIES if not policies.get(key, False))
        if disabled:
            risks.append("one or more safety policies are disabled")
            return self._blocked(RollbackStatus.BLOCKED_POLICY_VIOLATION.value, scope, policies, controls, tuple(f"enable_safety_policy:{key}" for key in disabled), risks, evidence_ids, "rollback cannot proceed while safety controls are disabled")
        if not validation_evidence_ids:
            required.append("validation_evidence_ids")
            risks.append("rollback behavior has not been evidenced in a validation environment")
        if not approved_change_window:
            required.append("approved_change_window")
        steps = self._steps(scope, controls)
        status = RollbackStatus.READY_FOR_REVIEW.value if not required else RollbackStatus.PREVIEW_ONLY.value
        plan_id = self._plan_id(scope, baseline_configs, current_configs, evidence_ids)
        return RollbackPlan(plan_id, status, scope, False, True, policies, controls, steps, tuple(dict.fromkeys(required)), tuple(dict.fromkeys(risks)), tuple(dict.fromkeys(str(item) for item in tuple(evidence_ids) + tuple(validation_evidence_ids))))

    @staticmethod
    def _steps(scope: tuple[str, ...], controls: tuple[str, ...]) -> tuple[RollbackStep, ...]:
        """Create policy-preserving rollback phases without device commands."""
        return (
            RollbackStep("rollback-precheck", "Rollback prechecks", scope, ("confirm approved scope", "confirm baseline artifact hashes", "confirm maintenance window"), ("current state captured",), tuple(f"verify {control} remains reachable" for control in controls), ("baseline artifact integrity",)),
            RollbackStep("rollback-restore", "Restore selected scope from baseline", scope, ("review baseline diff", "restore only approved scope", "retain unrelated changes"), ("rollback-precheck completed",), tuple(f"protect {control}" for control in controls), ("scoped change observation",)),
            RollbackStep("rollback-verify", "Verify after scoped rollback", scope, ("collect read-only discovery", "verify management and policy controls", "reconcile operational state"), ("rollback-restore reviewed",), tuple(f"confirm {control}" for control in controls), ("connectivity evidence", "service health evidence")),
        )

    @staticmethod
    def _plan_id(scope: tuple[str, ...], baseline: Mapping[str, Any], current: Mapping[str, Any], evidence_ids: Sequence[str]) -> str:
        """Create a deterministic rollback plan identifier without serializing secrets."""
        payload = json.dumps({"scope": scope, "baseline_keys": sorted(baseline), "current_keys": sorted(current), "evidence": tuple(evidence_ids)}, sort_keys=True, default=str).encode("utf-8")
        return f"rollback-plan:{hashlib.sha256(payload).hexdigest()[:16]}"

    @staticmethod
    def _blocked(status: str, scope: tuple[str, ...], policies: Mapping[str, bool], controls: tuple[str, ...], required: Sequence[str], risks: Sequence[str], evidence_ids: Sequence[str], reason: str) -> RollbackPlan:
        """Create an explicit non-executable rollback result."""
        return RollbackPlan("rollback-plan:blocked", status, scope, False, True, dict(policies), controls, (), tuple(dict.fromkeys(str(item) for item in required)) + (reason,), tuple(dict.fromkeys(risks)), tuple(dict.fromkeys(str(item) for item in evidence_ids)))
