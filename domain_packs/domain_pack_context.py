from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DomainPackContext:
    """Traceable context for one workflow's domain-pack decision."""

    workflow_id: str
    requested_sector: str | None = None
    inferred_sector: str | None = None
    inference_confidence: float = 0.0
    review_required: bool = True
    selected_pack: str | None = None
    active_packs: list[str] = field(default_factory=list)
    source_of_truth: str = "requirements_document"
    general_rules: dict[str, Any] = field(default_factory=dict)
    sector_rules: dict[str, Any] = field(default_factory=dict)
    governance_rules: dict[str, Any] = field(default_factory=dict)
    compliance_rules: dict[str, Any] = field(default_factory=dict)
    evidence_ids: list[str] = field(default_factory=list)

    def trace(self) -> dict[str, Any]:
        """Return a serializable trace for review and downstream gates."""
        return {
            "workflow_id": self.workflow_id,
            "requested_sector": self.requested_sector,
            "inferred_sector": self.inferred_sector,
            "inference_confidence": self.inference_confidence,
            "review_required": self.review_required,
            "selected_pack": self.selected_pack,
            "active_packs": list(self.active_packs),
            "source_of_truth": self.source_of_truth,
            "evidence_ids": list(self.evidence_ids),
        }
