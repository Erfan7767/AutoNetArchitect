from __future__ import annotations

from typing import Any

from .domain_pack_registry import DomainPackRegistry


class SectorInference:
    """Infer a candidate sector without silently activating a production pack."""

    def __init__(self, registry: DomainPackRegistry | None = None) -> None:
        self.registry = registry or DomainPackRegistry()

    def infer(self, requirements: dict[str, Any]) -> dict[str, Any]:
        explicit = requirements.get("sector", requirements.get("organization_type"))
        if explicit:
            candidates = self.registry.find_by_sector(str(explicit))
            return {"sector": str(explicit).lower(), "confidence": 1.0 if len(candidates) == 1 else 0.0, "review_required": len(candidates) != 1, "basis": ["explicit_sector"], "candidate_packs": [record.pack_id for record in candidates], "status": "explicit" if len(candidates) == 1 else "unresolved"}
        signals = {str(key).lower(): str(value).lower() for key, value in requirements.get("sector_signals", {}).items()}
        scores = {record.pack_id: 0.0 for record in self.registry.list_records()}
        keyword_map = {
            "banking": ("bank", "atm", "payment", "teller"),
            "hospital_clinical": ("hospital", "clinical", "patient", "medical", "pacs"),
            "university_campus": ("university", "campus", "student", "research", "dormitory"),
            "enterprise_corporate": ("enterprise", "corporate", "branch", "hq", "office"),
        }
        text = " ".join(signals.values())
        for pack_id, keywords in keyword_map.items():
            scores[pack_id] = float(sum(1 for word in keywords if word in text))
        best = max(scores, key=scores.get) if scores else None
        best_score = scores.get(best, 0.0) if best else 0.0
        total = sum(scores.values())
        confidence = best_score / total if total else 0.0
        tied = [pack_id for pack_id, score in scores.items() if score == best_score and score > 0]
        return {"sector": best if len(tied) == 1 and confidence >= 0.6 else None, "confidence": round(confidence, 3), "review_required": True, "basis": ["sector_signals"] if total else [], "candidate_packs": tied, "scores": scores, "status": "inferred" if len(tied) == 1 and confidence >= 0.6 else "ambiguous_or_unknown"}
