"""Detection of recurring discrepancy and failure patterns."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .discrepancy_registry import DiscrepancyRecord, DiscrepancyType
from .failure_memory import FailureMemoryEntry


class RecurrencePattern(BaseModel):
    """A repeated pattern suitable for lesson and benchmarking review."""

    model_config = ConfigDict(extra="forbid")

    pattern_id: str = Field(min_length=1)
    fingerprint: str = Field(min_length=1)
    discrepancy_type: DiscrepancyType
    scenario_ids: tuple[str, ...] = ()
    decision_ids: tuple[str, ...] = ()
    discrepancy_ids: tuple[str, ...] = ()
    failure_ids: tuple[str, ...] = ()
    occurrence_count: int
    threshold_reached: bool
    recurring_human_correction: bool = False
    summary: str = ""
    required_action: str = ""


class RecurrenceDetector(BaseDesigner):
    """Group similar failures while retaining links to every occurrence."""

    def __init__(self, threshold: int = 2) -> None:
        """Initialize detector with an explicit recurrence threshold."""
        super().__init__("RecurrenceDetector")
        if threshold < 2:
            raise ValueError("recurrence threshold must be at least two")
        self.threshold = threshold
        self.record_decision("recurrence_threshold", threshold, "recurrence patterns are surfaced only after the configured minimum occurrences")

    def detect(self, discrepancies: Iterable[DiscrepancyRecord] = (), failures: Iterable[FailureMemoryEntry] = ()) -> tuple[RecurrencePattern, ...]:
        """Detect patterns from discrepancies and failure memory."""
        discrepancy_items = tuple(discrepancies)
        failure_items = tuple(failures)
        by_key: dict[str, list[DiscrepancyRecord]] = defaultdict(list)
        for record in discrepancy_items:
            by_key[self.fingerprint(record)].append(record)
        failure_by_discrepancy = {item.discrepancy_id: item for item in failure_items}
        patterns: list[RecurrencePattern] = []
        for fingerprint, items in sorted(by_key.items()):
            related_failures = [failure_by_discrepancy[item.discrepancy_id] for item in items if item.discrepancy_id in failure_by_discrepancy]
            count = sum(item.occurrence_count for item in related_failures) or len(items)
            corrections = any(item.human_correction is not None for item in items)
            pattern = RecurrencePattern(pattern_id=f"pattern:{fingerprint}", fingerprint=fingerprint, discrepancy_type=items[0].discrepancy_type, scenario_ids=tuple(dict.fromkeys(item.scenario_id for item in items)), decision_ids=tuple(dict.fromkeys(item.decision_id for item in items)), discrepancy_ids=tuple(item.discrepancy_id for item in items), failure_ids=tuple(item.failure_id for item in related_failures), occurrence_count=count, threshold_reached=count >= self.threshold, recurring_human_correction=corrections, summary=f"{items[0].discrepancy_type.value} recurrence across {count} recorded occurrence(s)", required_action="create or update a reviewed lesson and add prevention control" if count >= self.threshold else "continue evidence collection")
            patterns.append(pattern)
        self.record_decision("recurrence_detection", len(patterns), "patterns retain all scenario, decision, failure, and correction references")
        return tuple(patterns)

    @staticmethod
    def fingerprint(record: DiscrepancyRecord) -> str:
        """Build a conservative fingerprint from explicit categorical evidence."""
        return "|".join((record.discrepancy_type.value, record.scenario_id, record.decision_id, record.actual_outcome.status, record.evidence_state))
