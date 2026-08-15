from __future__ import annotations

from typing import Any

from designers.base_designer import BaseDesigner

from .domain_pack_registry import DomainPackRegistry
from .sector_inference import SectorInference


class DomainPackSelector(BaseDesigner):
    """Select one candidate pack with explicit confidence and review state."""

    def __init__(self, registry: DomainPackRegistry | None = None) -> None:
        super().__init__()
        self.registry = registry or DomainPackRegistry()
        self.inference = SectorInference(self.registry)

    def select(self, requirements: dict[str, Any]) -> dict[str, Any]:
        inference = self.inference.infer(requirements)
        candidates = inference.get("candidate_packs", [])
        selected = candidates[0] if len(candidates) == 1 and inference.get("confidence", 0.0) >= 0.6 else None
        review = True
        self.record_decision("domain_pack_selection", selected or "no_production_selection", "Select only one traceable candidate and require review for inference uncertainty.", alternatives=candidates, rejection_reasons={candidate: "confidence or ambiguity requires review" for candidate in candidates if candidate != selected})
        return {"selected_pack": selected, "inference": inference, "review_required": review, "status": "selected_pending_review" if selected and review else "selected" if selected else "no_decision", "decision_records": list(self.decisions)}

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        return self.select(requirements)
