"""Persistent failure memory built from discrepancy records."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .discrepancy_registry import DiscrepancyRecord, DiscrepancySeverity, DiscrepancyType


class FailureMemoryEntry(BaseModel):
    """A failure retained for future knowledge and benchmarking consumption."""

    model_config = ConfigDict(extra="forbid")

    failure_id: str = Field(min_length=1)
    discrepancy_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    failure_type: DiscrepancyType
    severity: DiscrepancySeverity
    actual_status: str
    actual_summary: str
    evidence_state: str
    evidence_ids: tuple[str, ...] = ()
    human_correction_id: str | None = None
    lesson_id: str | None = None
    postmortem_id: str | None = None
    occurrence_count: int = 1
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    retained_for_learning: bool = True


class FailureMemory(BaseDesigner):
    """Store and query failures without erasing prior outcomes."""

    def __init__(self) -> None:
        """Initialize failure memory."""
        super().__init__("FailureMemory")
        self._entries: dict[str, FailureMemoryEntry] = {}
        self.record_decision("failure_memory_policy", "failures_are_retained", "a failure remains available for lessons, recurrence detection, and benchmarking")

    def record(self, discrepancy: DiscrepancyRecord, *, failure_id: str | None = None) -> FailureMemoryEntry:
        """Create or increment failure memory for a discrepancy."""
        identifier = failure_id or f"failure:{discrepancy.discrepancy_id}"
        current = self._entries.get(identifier)
        if current is not None:
            updated = current.model_copy(update={"occurrence_count": current.occurrence_count + 1, "last_seen_at": datetime.now(timezone.utc), "evidence_ids": tuple(dict.fromkeys(current.evidence_ids + discrepancy.evidence_ids))})
            self._entries[identifier] = updated
            self.record_decision(f"failure_repeat:{identifier}", updated.occurrence_count, "recurring failure was retained as an incremented memory entry")
            return updated
        entry = FailureMemoryEntry(failure_id=identifier, discrepancy_id=discrepancy.discrepancy_id, scenario_id=discrepancy.scenario_id, decision_id=discrepancy.decision_id, failure_type=discrepancy.discrepancy_type, severity=discrepancy.severity, actual_status=discrepancy.actual_outcome.status, actual_summary=discrepancy.actual_outcome.summary, evidence_state=discrepancy.evidence_state, evidence_ids=tuple(dict.fromkeys(discrepancy.evidence_ids + discrepancy.actual_outcome.evidence_ids)), human_correction_id=discrepancy.human_correction.correction_id if discrepancy.human_correction else None)
        self._entries[identifier] = entry
        self.record_decision(f"failure:{identifier}", entry.failure_type.value, "failure was linked to the original discrepancy and actual outcome")
        return entry

    def link_lesson(self, failure_id: str, lesson_id: str) -> FailureMemoryEntry:
        """Link a reviewed lesson to failure memory."""
        if not lesson_id.strip():
            raise ValueError("lesson_id is mandatory")
        current = self._entries[failure_id]
        updated = current.model_copy(update={"lesson_id": lesson_id})
        self._entries[failure_id] = updated
        return updated

    def link_postmortem(self, failure_id: str, postmortem_id: str) -> FailureMemoryEntry:
        """Link a postmortem to failure memory."""
        if not postmortem_id.strip():
            raise ValueError("postmortem_id is mandatory")
        current = self._entries[failure_id]
        updated = current.model_copy(update={"postmortem_id": postmortem_id})
        self._entries[failure_id] = updated
        return updated

    def all(self) -> tuple[FailureMemoryEntry, ...]:
        """Return all failure entries."""
        return tuple(self._entries.values())

    def recurring(self, minimum_occurrences: int = 2) -> tuple[FailureMemoryEntry, ...]:
        """Return repeated failures at or above a threshold."""
        if minimum_occurrences < 2:
            raise ValueError("minimum_occurrences must be at least two")
        return tuple(item for item in self._entries.values() if item.occurrence_count >= minimum_occurrences)
