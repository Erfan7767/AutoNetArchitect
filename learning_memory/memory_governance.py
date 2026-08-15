"""Governance for publishing and consuming learning memory."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner

from .lesson_model import EvidenceStatus, LessonRecord, LessonStatus


class MemoryGovernanceDecision(BaseModel):
    """Decision about whether a lesson may be published to consumers."""

    model_config = ConfigDict(extra="forbid")

    lesson_id: str
    allowed: bool
    status: LessonStatus
    reasons: tuple[str, ...] = ()
    required_actions: tuple[str, ...] = ()


class MemoryGovernance(BaseDesigner):
    """Prevent unreviewed memory from silently becoming production knowledge."""

    def __init__(self) -> None:
        """Initialize memory governance."""
        super().__init__("MemoryGovernance")
        self._published: dict[str, LessonRecord] = {}
        self.record_decision("memory_publication_policy", "review_and_evidence_required", "lessons require evidence and human review before knowledge consumers may treat them as published")

    def assess_publication(self, lesson: LessonRecord) -> MemoryGovernanceDecision:
        """Assess lesson publication eligibility."""
        reasons: list[str] = []
        actions: list[str] = []
        if lesson.evidence_status not in {EvidenceStatus.VERIFIED, EvidenceStatus.PARTIALLY_VERIFIED}:
            reasons.append("lesson evidence is not verified or partially verified")
            actions.append("collect and review evidence")
        if not lesson.evidence_ids:
            reasons.append("lesson has no evidence identifiers")
            actions.append("link evidence records")
        if lesson.status not in {LessonStatus.VALIDATED, LessonStatus.PUBLISHED}:
            reasons.append("lesson has not completed human validation")
            actions.append("complete human lesson review")
        allowed = not reasons
        status = LessonStatus.PUBLISHED if allowed else LessonStatus.REVIEW_REQUIRED
        self.record_decision(f"lesson_publication:{lesson.lesson_id}", status.value, "publication is governed by evidence and review state")
        return MemoryGovernanceDecision(lesson_id=lesson.lesson_id, allowed=allowed, status=status, reasons=tuple(reasons), required_actions=tuple(actions))

    def publish(self, lesson: LessonRecord) -> LessonRecord:
        """Publish a lesson only after the governance assessment allows it."""
        decision = self.assess_publication(lesson)
        if not decision.allowed:
            raise ValueError(f"lesson cannot be published: {'; '.join(decision.reasons)}")
        published = lesson.model_copy(update={"status": LessonStatus.PUBLISHED})
        self._published[lesson.lesson_id] = published
        return published

    def published(self) -> tuple[LessonRecord, ...]:
        """Return lessons available to downstream consumers."""
        return tuple(self._published.values())
