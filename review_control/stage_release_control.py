"""Stage release control backed by formal go/no-go outcomes."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .go_no_go_engine import GoNoGoEngine
from .mandatory_checkpoints import CheckpointRecord
from .no_go_policy import NoGoBlocker, NoGoEvaluation, NoGoOutcome


class StageReleaseRequest(BaseModel):
    """Request to release an artifact or stage to its next lifecycle state."""

    model_config = ConfigDict(extra="forbid")

    stage: str = Field(min_length=1)
    release_target: str = Field(min_length=1)
    checkpoint_records: tuple[CheckpointRecord, ...] = ()
    blockers: tuple[NoGoBlocker, ...] = ()
    production_requested: bool = False
    approval_present: bool = False
    governance_reference: str = ""


class StageReleaseController(BaseDesigner):
    """Prevent stage release when mandatory controls are not satisfied."""

    def __init__(self, *, engine: GoNoGoEngine | None = None) -> None:
        """Initialize release controller."""
        super().__init__("StageReleaseController")
        self.engine = engine or GoNoGoEngine()
        self.record_decision("stage_release_default", "no_go_until_mandatory_controls_resolved", "release target cannot bypass formal checkpoint or blocker evaluation")

    def assess(self, request: StageReleaseRequest) -> NoGoEvaluation:
        """Assess a release request without changing project state."""
        evaluation = self.engine.evaluate(stage=request.stage, checkpoint_records=request.checkpoint_records, blockers=request.blockers, production_requested=request.production_requested, approval_present=request.approval_present, governance_reference=request.governance_reference)
        self.record_decision(f"release_assess:{request.stage}:{request.release_target}", evaluation.outcome.value, "stage release assessment remains separate from execution")
        return evaluation

    def release(self, request: StageReleaseRequest) -> NoGoEvaluation:
        """Release only when the formal outcome allows it."""
        evaluation = self.assess(request)
        if evaluation.outcome == NoGoOutcome.NO_GO or (request.production_requested and not evaluation.production_release_allowed):
            self.record_decision(f"release_block:{request.stage}:{request.release_target}", "no_go", "stage release was stopped by formal no-go enforcement")
            raise RuntimeError(f"NO-GO release blocked for {request.stage}:{request.release_target}")
        self.record_decision(f"release:{request.stage}:{request.release_target}", evaluation.outcome.value, "stage release is allowed only after formal go/no-go assessment")
        return evaluation
