"""Go/no-go aggregation and enforcement engine."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner

from .mandatory_checkpoints import CheckpointRecord, MandatoryCheckpointRegistry
from .no_go_policy import NoGoBlocker, NoGoEvaluation, NoGoOutcome, NoGoPolicy


class NoGoEnforcedError(RuntimeError):
    """Raised when a stage release is attempted while formal no-go conditions exist."""


class GoNoGoEngine(BaseDesigner):
    """Evaluate and enforce mandatory release checkpoints."""

    def __init__(self, *, registry: MandatoryCheckpointRegistry | None = None, policy: NoGoPolicy | None = None) -> None:
        """Initialize engine with registry and no-go policy."""
        super().__init__("GoNoGoEngine")
        self.registry = registry or MandatoryCheckpointRegistry()
        self.policy = policy or NoGoPolicy()
        self.record_decision("go_no_go_enforcement", "formal_release_outcome", "stage releases must consume a formal no-go evaluation")

    def evaluate(self, *, stage: str, checkpoint_records: Iterable[CheckpointRecord] = (), blockers: Iterable[NoGoBlocker] = (), production_requested: bool = False, approval_present: bool = False, governance_reference: str = "") -> NoGoEvaluation:
        """Evaluate all mandatory checkpoints for a stage."""
        definitions = self.registry.for_stage(stage)
        records = {item.checkpoint_id: item for item in checkpoint_records}
        unresolved: list[str] = []
        for definition in definitions:
            record = records.get(definition.checkpoint_id)
            if record is None or not record.is_release_ready(definition):
                unresolved.append(definition.checkpoint_id)
        evaluation = self.policy.evaluate(stage=stage, blockers=blockers, unresolved_checkpoint_ids=unresolved, required_checkpoint_ids=tuple(item.checkpoint_id for item in definitions), approval_present=approval_present, production_requested=production_requested, governance_reference=governance_reference)
        self.record_decision(f"stage_evaluation:{stage}", evaluation.outcome.value, "mandatory checkpoint records and blocker states were evaluated before release")
        return evaluation

    def enforce(self, evaluation: NoGoEvaluation) -> NoGoEvaluation:
        """Raise a formal exception for no-go or unresolved production release."""
        if evaluation.outcome == NoGoOutcome.NO_GO or not evaluation.production_release_allowed and evaluation.stage in {"deployment", "config_generation", "design", "final_design"}:
            raise NoGoEnforcedError(f"NO-GO for {evaluation.stage}: {'; '.join(evaluation.reasons) or 'mandatory checkpoint unresolved'}")
        return evaluation
