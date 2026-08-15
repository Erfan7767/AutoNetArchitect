"""Formal no-go blocker policy."""
from __future__ import annotations

from enum import Enum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner


class BlockerClass(str, Enum):
    """Classes of conditions that can prevent stage release."""

    HUMAN_DATA = "human_data"
    UNSUPPORTED_SCOPE = "unsupported_scope"
    EVIDENCE = "evidence"
    DESIGN = "design"
    EQUIPMENT = "equipment"
    CONFIGURATION = "configuration"
    DEPLOYMENT = "deployment"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    GOVERNANCE = "governance"
    VERIFICATION = "verification"


class NoGoOutcome(str, Enum):
    """Formal release outcomes."""

    GO = "go"
    GO_WITH_CONDITIONS = "go_with_conditions"
    NO_GO = "no_go"
    PENDING_REVIEW = "pending_review"


class NoGoBlocker(BaseModel):
    """Formal no-go outcome detail, not a warning."""

    model_config = ConfigDict(extra="forbid")

    blocker_id: str = Field(min_length=1)
    blocker_class: BlockerClass
    blocking_reason: str = Field(min_length=1)
    affected_stage: str = Field(min_length=1)
    required_resolution: str = Field(min_length=1)
    affected_artifacts: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    owner_role: str = "engineer_in_charge"
    resolved: bool = False
    resolution_reference: str = ""


class NoGoEvaluation(BaseModel):
    """Aggregate formal go/no-go result."""

    model_config = ConfigDict(extra="forbid")

    stage: str
    outcome: NoGoOutcome
    blockers: tuple[NoGoBlocker, ...] = ()
    required_checkpoints: tuple[str, ...] = ()
    unresolved_checkpoint_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    governance_reference: str = ""
    production_release_allowed: bool = False


class NoGoPolicy(BaseDesigner):
    """Convert unresolved checkpoint and blocker states into formal release outcomes."""

    def __init__(self) -> None:
        """Initialize no-go policy with deny-by-default release behavior."""
        super().__init__("NoGoPolicy")
        self.record_decision("no_go_default", NoGoOutcome.NO_GO.value, "production release is denied until mandatory checkpoints and blockers are resolved")

    def evaluate(self, *, stage: str, blockers: Iterable[NoGoBlocker] = (), unresolved_checkpoint_ids: Iterable[str] = (), required_checkpoint_ids: Iterable[str] = (), approval_present: bool = False, production_requested: bool = False, governance_reference: str = "") -> NoGoEvaluation:
        """Return a formal outcome for a stage release."""
        blocker_items = tuple(blockers)
        unresolved = tuple(dict.fromkeys(str(item) for item in unresolved_checkpoint_ids))
        required = tuple(dict.fromkeys(str(item) for item in required_checkpoint_ids))
        reasons: list[str] = []
        if blocker_items:
            reasons.extend(f"blocker {item.blocker_id}: {item.blocking_reason}" for item in blocker_items if not item.resolved)
        if unresolved:
            reasons.append("mandatory checkpoints remain unresolved")
        if production_requested and not approval_present:
            reasons.append("production release requires explicit approval")
        if reasons:
            outcome = NoGoOutcome.NO_GO
        elif production_requested and approval_present:
            outcome = NoGoOutcome.GO
        elif not production_requested:
            outcome = NoGoOutcome.GO_WITH_CONDITIONS
        else:
            outcome = NoGoOutcome.GO_WITH_CONDITIONS
        production_allowed = outcome in {NoGoOutcome.GO, NoGoOutcome.GO_WITH_CONDITIONS} and not unresolved and not any(not item.resolved for item in blocker_items)
        if production_requested and outcome != NoGoOutcome.GO:
            production_allowed = False
        self.record_decision(f"no_go:{stage}", outcome.value, "formal outcome is derived from unresolved blockers, checkpoints, and explicit approval")
        return NoGoEvaluation(stage=stage, outcome=outcome, blockers=blocker_items, required_checkpoints=required, unresolved_checkpoint_ids=unresolved, reasons=tuple(dict.fromkeys(reasons)), governance_reference=governance_reference, production_release_allowed=production_allowed)
