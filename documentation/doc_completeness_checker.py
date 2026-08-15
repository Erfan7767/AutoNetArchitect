"""Completeness and freshness gates for generated documentation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from .doc_models import CompletenessResult, DocumentType, ResolvedData, SectionStatus


class DocCompletenessChecker:
    """Assess section completeness and apply configurable rendering gates."""

    def __init__(self, *, stale_after_days: int = 90) -> None:
        """Configure the age threshold for source timestamps."""
        if stale_after_days < 1:
            raise ValueError("stale_after_days must be positive")
        self.stale_after_days = stale_after_days

    def check(self, resolved: ResolvedData, *, minimum_score: float = 0.0, allow_pending: bool = True) -> CompletenessResult:
        """Return a structured result without silently removing incomplete sections."""
        blocking: list[str] = []
        pending = list(resolved.pending_sections)
        stale = list(resolved.stale_sections)
        for item in resolved.sections:
            if item.section.mandatory and item.status == SectionStatus.PENDING:
                blocking.append(f"mandatory section pending: {item.section.section_id}")
            if item.status == SectionStatus.PENDING and not allow_pending:
                blocking.append(f"pending sections are disabled: {item.section.section_id}")
            if self._is_stale(item.source_timestamps):
                stale.append(item.section.section_id)
        if resolved.completeness_score < minimum_score:
            blocking.append(f"completeness score {resolved.completeness_score} below minimum {minimum_score}")
        mandatory_complete = resolved.mandatory_sections_complete
        can_render = not blocking
        return CompletenessResult(document_type=resolved.document_type, completeness_score=resolved.completeness_score, mandatory_sections_complete=mandatory_complete, pending_sections=sorted(set(pending)), stale_sections=sorted(set(stale)), blocking_reasons=blocking, can_render=can_render)

    def _is_stale(self, timestamps: Iterable[str]) -> bool:
        """Determine whether any supplied timestamp is older than the threshold."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.stale_after_days)
        for raw in timestamps:
            try:
                value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            if value < cutoff:
                return True
        return False
