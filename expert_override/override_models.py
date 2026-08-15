"""Contracts for explicit expert intervention and override provenance."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OverrideType(str, Enum):
    """Supported human intervention actions."""

    FORCE_ACCEPT = "force_accept"
    FORCE_REJECT = "force_reject"
    MODIFY_VALUE = "modify_value"
    NARROW_SCOPE = "narrow_scope"
    WIDEN_SCOPE_WITH_WARNING = "widen_scope_with_warning"
    DEFER_DECISION = "defer_decision"
    REPLACE_RECOMMENDATION = "replace_recommendation"


class OverrideTargetType(str, Enum):
    """Artifact classes that may receive an expert override."""

    REQUIREMENT = "requirement"
    DESIGN_DECISION = "design_decision"
    EQUIPMENT_SELECTION = "equipment_selection"
    CONFIG_ARTIFACT = "config_artifact"
    DEPLOYMENT_GATE = "deployment_gate"
    OPERATIONAL_POLICY = "operational_policy"


class DecisionOrigin(str, Enum):
    """Origin classification for the resulting decision."""

    MACHINE_MADE = "machine_made"
    HUMAN_OVERRIDDEN = "human_overridden"
    HUMAN_ORIGINATED = "human_originated"


class RevalidationStatus(str, Enum):
    """State of dependency revalidation after an override."""

    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class OverrideScope(BaseModel):
    """Explicit scope of an intervention."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1)
    workflow: str = Field(min_length=1)
    target_ids: tuple[str, ...] = ()
    device_ids: tuple[str, ...] = ()
    site_ids: tuple[str, ...] = ()
    environment: str = "design"
    scope_statement: str = Field(min_length=1)


class OverrideRequest(BaseModel):
    """Human-submitted override request that never mutates an artifact silently."""

    model_config = ConfigDict(extra="forbid")

    override_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    target_type: OverrideTargetType
    override_type: OverrideType
    scope: OverrideScope
    actor_id: str = Field(min_length=1)
    actor_role: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    impact: str = Field(min_length=1)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    machine_decision_id: str | None = None
    original_value: Any = None
    proposed_value: Any = None
    affected_artifact_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    warning: str = ""
    rationale_id: str | None = None
    requires_revalidation: bool = True
    approval_reference: str = ""


class OverrideApplication(BaseModel):
    """Immutable result preserving original and resulting decision provenance."""

    model_config = ConfigDict(extra="forbid")

    override_id: str
    target_id: str
    target_type: OverrideTargetType
    override_type: OverrideType
    status: str
    origin: DecisionOrigin
    machine_decision_id: str | None = None
    resulting_value: Any = None
    original_value: Any = None
    provenance_chain: tuple[str, ...] = ()
    actor_id: str
    actor_role: str
    reason: str
    scope: OverrideScope
    impact: str
    decided_at: datetime
    revalidation_status: RevalidationStatus
    revalidation_trigger_ids: tuple[str, ...] = ()
    affected_artifact_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    rejection_reasons: tuple[str, ...] = ()

    @property
    def human_intervention(self) -> bool:
        """Return whether a human changed or originated the decision."""
        return self.origin in {DecisionOrigin.HUMAN_OVERRIDDEN, DecisionOrigin.HUMAN_ORIGINATED}

    def provenance(self) -> dict[str, Any]:
        """Return a compact provenance view suitable for downstream artifacts."""
        return {"origin": self.origin.value, "machine_decision_id": self.machine_decision_id, "override_id": self.override_id, "provenance_chain": list(self.provenance_chain), "revalidation_status": self.revalidation_status.value}
