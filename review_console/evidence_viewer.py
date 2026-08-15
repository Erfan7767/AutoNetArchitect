"""Presentation adapter for traceable evidence."""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner


class EvidenceItemView(BaseModel):
    """Evidence item shown in the console."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    source_type: str = "unknown"
    claim_type: str = "unknown"
    claim_value: Any = None
    confidence: float | None = None
    freshness_expiry: date | None = None
    support_scope: str | None = None
    region_scope: str | None = None
    revoked: bool = False
    status: str = "unknown"
    trace_reference: str = ""


class EvidenceViewer(BaseDesigner):
    """Render evidence records without resolving or ranking them."""

    def __init__(self) -> None:
        """Initialize evidence viewer."""
        super().__init__("EvidenceViewer")
        self.record_decision("evidence_view_policy", "trace_only", "console presents evidence metadata and delegates authority/freshness to knowledge services")

    def build(self, evidence: Iterable[Any] = (), evidence_ids: Iterable[str] = ()) -> tuple[EvidenceItemView, ...]:
        """Build evidence views from EvidenceRecord objects or compatible dictionaries."""
        rows: list[EvidenceItemView] = []
        seen: set[str] = set()
        for item in evidence:
            data = item if isinstance(item, dict) else self._model_data(item)
            evidence_id = str(data.get("source_id", data.get("evidence_id", "unknown")))
            seen.add(evidence_id)
            expiry = data.get("freshness_expiry")
            rows.append(EvidenceItemView(evidence_id=evidence_id, source_type=str(data.get("source_type", "unknown")), claim_type=str(data.get("claim_type", "unknown")), claim_value=data.get("claim_value"), confidence=data.get("confidence"), freshness_expiry=expiry, support_scope=data.get("support_scope"), region_scope=data.get("region_scope"), revoked=bool(data.get("revoked", False)), status=self._status(data), trace_reference=f"evidence://{evidence_id}"))
        for identifier in evidence_ids:
            value = str(identifier)
            if value not in seen:
                rows.append(EvidenceItemView(evidence_id=value, status="referenced_not_loaded", trace_reference=f"evidence://{value}"))
        return tuple(rows)

    @staticmethod
    def _model_data(item: Any) -> dict[str, Any]:
        """Read Pydantic model data without coupling to one concrete evidence class."""
        if hasattr(item, "model_dump"):
            return dict(item.model_dump())
        return {key: getattr(item, key) for key in dir(item) if not key.startswith("_") and key in {"source_id", "evidence_id", "source_type", "claim_type", "claim_value", "confidence", "freshness_expiry", "support_scope", "region_scope", "revoked"}}

    @staticmethod
    def _status(data: dict[str, Any]) -> str:
        """Derive a display status from explicit evidence fields only."""
        if data.get("revoked"):
            return "revoked"
        expiry = data.get("freshness_expiry")
        if isinstance(expiry, date) and expiry < date.today():
            return "stale"
        return "active"
