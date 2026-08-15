"""Extraction of recurring human correction patterns."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .discrepancy_registry import DiscrepancyRecord


class CorrectionPattern(BaseModel):
    """A repeated human correction pattern."""

    model_config = ConfigDict(extra="forbid")

    pattern_id: str = Field(min_length=1)
    action_signature: str = Field(min_length=1)
    correction_ids: tuple[str, ...] = ()
    discrepancy_ids: tuple[str, ...] = ()
    target_types: tuple[str, ...] = ()
    occurrence_count: int
    outcome_statuses: tuple[str, ...] = ()
    reuse_recommendation: str
    evidence_ids: tuple[str, ...] = ()


class CorrectionPatternDetector(BaseDesigner):
    """Group human corrections without treating them as automatic truth."""

    def __init__(self, threshold: int = 2) -> None:
        """Initialize correction detector."""
        super().__init__("CorrectionPatternDetector")
        if threshold < 2:
            raise ValueError("correction threshold must be at least two")
        self.threshold = threshold
        self.record_decision("correction_pattern_policy", "human_patterns_require_review", "repeated human corrections become candidate lessons and never auto-change production rules")

    def detect(self, discrepancies: Iterable[DiscrepancyRecord]) -> tuple[CorrectionPattern, ...]:
        """Detect repeated correction actions."""
        groups: dict[str, list[DiscrepancyRecord]] = defaultdict(list)
        for record in discrepancies:
            if record.human_correction is not None:
                signature = f"{record.discrepancy_type.value}|{record.human_correction.action}"
                groups[signature].append(record)
        patterns: list[CorrectionPattern] = []
        for signature, records in sorted(groups.items()):
            corrections = [record.human_correction for record in records if record.human_correction is not None]
            evidence = tuple(dict.fromkeys(evidence_id for record in records for evidence_id in record.evidence_ids + record.actual_outcome.evidence_ids + (record.human_correction.evidence_ids if record.human_correction else ())))
            count = len(records)
            patterns.append(CorrectionPattern(pattern_id=f"correction:{signature}", action_signature=signature, correction_ids=tuple(item.correction_id for item in corrections), discrepancy_ids=tuple(item.discrepancy_id for item in records), target_types=tuple(dict.fromkeys(item.discrepancy_type.value for item in records)), occurrence_count=count, outcome_statuses=tuple(dict.fromkeys(item.actual_outcome.status for item in records)), reuse_recommendation="candidate for reviewed prevention control" if count >= self.threshold else "retain as local human feedback", evidence_ids=evidence))
        self.record_decision("correction_pattern_detection", len(patterns), "human correction patterns preserve every original discrepancy link")
        return tuple(patterns)
