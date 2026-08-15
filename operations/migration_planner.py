"""Brownfield-assisted migration planning with explicit safety boundaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Sequence


class MigrationStatus(str, Enum):
    """Planning outcomes for assisted brownfield migration."""

    PREVIEW_ONLY = "preview_only"
    BLOCKED_MISSING_HUMAN_DATA = "blocked_missing_human_data"
    BLOCKED_UNSUPPORTED_MODE = "blocked_unsupported_mode"
    BLOCKED_AMBIGUOUS_INVENTORY = "blocked_ambiguous_inventory"
    READY_FOR_REVIEW = "ready_for_review"


@dataclass(frozen=True)
class MigrationPhase:
    """One ordered migration phase with validation and rollback boundaries."""

    phase_id: str
    title: str
    scope: tuple[str, ...]
    actions: tuple[str, ...]
    prerequisites: tuple[str, ...]
    validation_checks: tuple[str, ...]
    rollback_scope: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the phase."""
        return asdict(self) | {"scope": list(self.scope), "actions": list(self.actions), "prerequisites": list(self.prerequisites), "validation_checks": list(self.validation_checks), "rollback_scope": list(self.rollback_scope)}


@dataclass(frozen=True)
class MigrationPlan:
    """Non-executable migration plan with evidence and human review markers."""

    plan_id: str
    status: str
    mode: str
    production_execution_allowed: bool
    human_review_required: bool
    scope: tuple[str, ...]
    phases: tuple[MigrationPhase, ...]
    changed_fields: dict[str, tuple[str, ...]]
    safety_policies: dict[str, bool]
    required_human_inputs: tuple[str, ...]
    assumptions: tuple[str, ...]
    risk_reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the plan without embedding untrusted secrets."""
        return {
            "plan_id": self.plan_id,
            "status": self.status,
            "mode": self.mode,
            "production_execution_allowed": self.production_execution_allowed,
            "human_review_required": self.human_review_required,
            "scope": list(self.scope),
            "phases": [phase.to_dict() for phase in self.phases],
            "changed_fields": {key: list(value) for key, value in self.changed_fields.items()},
            "safety_policies": dict(self.safety_policies),
            "required_human_inputs": list(self.required_human_inputs),
            "assumptions": list(self.assumptions),
            "risk_reasons": list(self.risk_reasons),
            "evidence_ids": list(self.evidence_ids),
        }


class MigrationPlanner:
    """Build reviewable migration plans from current and target records.

    V1 intentionally stops at assisted planning. It does not connect to devices,
    execute changes, select an autonomous order for unknown dependencies, or claim
    that a migration is safe for production.
    """

    MODE = "brownfield_assisted"
    COMPARED_FIELDS = ("vendor", "platform", "model", "version", "hostname", "serial")
    SAFETY_DEFAULTS = {
        "preserve_management_access": True,
        "preserve_audit_logging": True,
        "abort_on_failed_validation": True,
        "retain_rollback_artifacts": True,
        "require_human_change_approval": True,
        "production_execution_disabled": True,
    }

    def plan(
        self,
        current_inventory: Mapping[str, Mapping[str, Any]] | None,
        target_design: Mapping[str, Mapping[str, Any]] | None,
        scope: Sequence[str] | None,
        *,
        mode: str = MODE,
        safety_policies: Mapping[str, bool] | None = None,
        evidence_ids: Sequence[str] = (),
        approved_change_window: str | None = None,
        lab_validation_evidence_ids: Sequence[str] = (),
    ) -> MigrationPlan:
        """Create a scoped brownfield migration plan without executing it."""
        normalized_scope = tuple(dict.fromkeys(str(item) for item in (scope or ()) if str(item)))
        policies = dict(self.SAFETY_DEFAULTS)
        policies.update({str(key): bool(value) for key, value in (safety_policies or {}).items()})
        missing: list[str] = []
        assumptions: list[str] = ["current inventory is treated as observed input only", "target design is treated as approved intent only"]
        risks: list[str] = ["V1 produces an assisted plan and never authorizes direct production execution"]
        if mode != self.MODE:
            return self._blocked("unsupported migration mode", MigrationStatus.BLOCKED_UNSUPPORTED_MODE.value, normalized_scope, policies, ("mode=brownfield_assisted",), assumptions, risks, evidence_ids)
        if not current_inventory:
            missing.append("current_inventory")
        if not target_design:
            missing.append("target_design")
        if not normalized_scope:
            missing.append("scope")
        if missing:
            return self._blocked("required migration inputs are missing", MigrationStatus.BLOCKED_MISSING_HUMAN_DATA.value, normalized_scope, policies, tuple(missing), assumptions, risks, evidence_ids)
        unknown_assets = tuple(asset_id for asset_id in normalized_scope if asset_id not in current_inventory or asset_id not in target_design)
        if unknown_assets:
            missing.extend(f"lifecycle_record:{asset_id}" for asset_id in unknown_assets)
            return self._blocked("scope contains an asset absent from current inventory or target design", MigrationStatus.BLOCKED_MISSING_HUMAN_DATA.value, normalized_scope, policies, tuple(missing), assumptions, risks, evidence_ids)
        ambiguous_assets = tuple(asset_id for asset_id in normalized_scope if self._is_ambiguous(current_inventory[asset_id]) or self._is_ambiguous(target_design[asset_id]))
        if ambiguous_assets:
            risks.append("ambiguous identity or confidence prevents an authoritative migration diff")
            return self._blocked("inventory or target design is ambiguous", MigrationStatus.BLOCKED_AMBIGUOUS_INVENTORY.value, normalized_scope, policies, tuple(f"authoritative_identity:{asset_id}" for asset_id in ambiguous_assets), assumptions, risks, evidence_ids)
        changed: dict[str, tuple[str, ...]] = {}
        for asset_id in normalized_scope:
            differences = tuple(field for field in self.COMPARED_FIELDS if self._value(current_inventory[asset_id], field) and self._value(target_design[asset_id], field) and self._value(current_inventory[asset_id], field) != self._value(target_design[asset_id], field))
            changed[asset_id] = differences
            if differences:
                risks.append(f"{asset_id} changes {', '.join(differences)}")
        if approved_change_window is None:
            missing.append("approved_change_window")
        if not lab_validation_evidence_ids:
            missing.append("lab_validation_evidence_ids")
        if not all(policies.get(key, False) for key in ("preserve_management_access", "preserve_audit_logging", "abort_on_failed_validation", "retain_rollback_artifacts", "require_human_change_approval", "production_execution_disabled")):
            missing.append("required_safety_policy_approval")
        phases = self._phases(normalized_scope, changed)
        status = MigrationStatus.PREVIEW_ONLY.value if missing else MigrationStatus.READY_FOR_REVIEW.value
        if missing:
            assumptions.append("missing human approvals keep this artifact at review-only status")
        plan_id = self._plan_id(normalized_scope, changed, evidence_ids)
        return MigrationPlan(plan_id, status, self.MODE, False, True, normalized_scope, phases, changed, policies, tuple(dict.fromkeys(missing)), tuple(dict.fromkeys(assumptions)), tuple(dict.fromkeys(risks)), tuple(dict.fromkeys(str(item) for item in evidence_ids)))

    def _phases(self, scope: tuple[str, ...], changed: Mapping[str, tuple[str, ...]]) -> tuple[MigrationPhase, ...]:
        """Build deterministic planning phases without choosing unprovided dependencies."""
        return (
            MigrationPhase("precheck", "Pre-change evidence and safety prechecks", scope, ("confirm approved scope", "capture current-state evidence", "verify management access", "verify rollback artifacts"), ("current inventory", "approved target design", "human change approval"), ("inventory identity verified", "management path verified", "rollback artifact integrity verified"), scope),
            MigrationPhase("change", "Scoped brownfield migration actions", scope, tuple(f"review target diff for {asset_id}" for asset_id in scope if changed.get(asset_id)), ("precheck completed", "maintenance window confirmed", "lab validation evidence reviewed"), ("device identity", "configuration intent", "service health", "connectivity intent"), scope),
            MigrationPhase("postcheck", "Post-change observation and reconciliation", scope, ("collect read-only discovery", "reconcile design and operational state", "record deviations"), ("change phase reviewed", "verification evidence available"), ("post-change discovery", "connectivity evidence", "rollback decision point"), scope),
        )

    @staticmethod
    def _is_ambiguous(record: Mapping[str, Any]) -> bool:
        """Recognize explicit uncertainty markers without interpreting silence as certainty."""
        return str(record.get("status", "")).lower() in {"ambiguous", "unknown_device", "unsupported_vendor", "insufficient_evidence"} or str(record.get("confidence", "")).lower() in {"ambiguous", "unknown"}

    @staticmethod
    def _value(record: Mapping[str, Any], field_name: str) -> str:
        """Return a normalized non-secret identity value."""
        value = record.get(field_name, "")
        return str(value).strip() if value is not None else ""

    @staticmethod
    def _plan_id(scope: tuple[str, ...], changed: Mapping[str, tuple[str, ...]], evidence_ids: Sequence[str]) -> str:
        """Create a deterministic plan identifier from explicit inputs."""
        payload = json.dumps({"scope": scope, "changed": changed, "evidence": tuple(evidence_ids)}, sort_keys=True, default=str).encode("utf-8")
        return f"migration-plan:{hashlib.sha256(payload).hexdigest()[:16]}"

    @staticmethod
    def _blocked(reason: str, status: str, scope: tuple[str, ...], policies: Mapping[str, bool], required: tuple[str, ...], assumptions: Sequence[str], risks: Sequence[str], evidence_ids: Sequence[str]) -> MigrationPlan:
        """Create an explicit non-executable blocked plan."""
        return MigrationPlan("migration-plan:blocked", status, MigrationPlanner.MODE, False, True, scope, (), {}, dict(policies), required, tuple(assumptions) + (reason,), tuple(risks), tuple(dict.fromkeys(str(item) for item in evidence_ids)))
