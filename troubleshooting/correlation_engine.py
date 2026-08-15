"""Multi-source evidence correlation without overclaiming causality."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field


class CorrelationLink(BaseModel):
    """One bounded correlation between evidence records."""

    model_config = ConfigDict(extra="forbid")

    correlation_id: str
    correlation_type: str
    source_ids: list[str] = Field(default_factory=list)
    strength: str
    rationale: str
    causal_claim: bool = False


class CorrelationReport(BaseModel):
    """Correlation report with explicit non-causal default."""

    model_config = ConfigDict(extra="forbid")

    links: list[CorrelationLink] = Field(default_factory=list)
    strongest_signal: str = "none"
    confidence: float = 0.0
    limitations: list[str] = Field(default_factory=list)
    decision_id: str


class CorrelationEngine:
    """Correlate evidence by explicit time, location, path, or change metadata."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def correlate(self, evidence: Iterable[Mapping[str, Any]], *, window_seconds: float = 300.0) -> CorrelationReport:
        """Build temporal, spatial, and change links from supplied mappings."""
        records = [dict(item) for item in evidence]
        links: list[CorrelationLink] = []
        for index, first in enumerate(records):
            first_id = str(first.get("evidence_id", f"evidence:{index}"))
            for second_index in range(index + 1, len(records)):
                second = records[second_index]
                second_id = str(second.get("evidence_id", f"evidence:{second_index}"))
                if first.get("device_id") and first.get("device_id") == second.get("device_id"):
                    links.append(CorrelationLink(correlation_id=f"spatial:{first_id}:{second_id}", correlation_type="spatial_same_device", source_ids=[first_id, second_id], strength="medium", rationale="both records identify the same device", causal_claim=False))
                if first.get("site_id") and first.get("site_id") == second.get("site_id"):
                    links.append(CorrelationLink(correlation_id=f"site:{first_id}:{second_id}", correlation_type="spatial_same_site", source_ids=[first_id, second_id], strength="low", rationale="both records identify the same site", causal_claim=False))
                first_time = self._time(first.get("timestamp", first.get("collected_at")))
                second_time = self._time(second.get("timestamp", second.get("collected_at")))
                if first_time and second_time and abs((first_time - second_time).total_seconds()) <= window_seconds:
                    links.append(CorrelationLink(correlation_id=f"time:{first_id}:{second_id}", correlation_type="temporal", source_ids=[first_id, second_id], strength="medium", rationale="records occur within the supplied time window", causal_claim=False))
                if first.get("change_id") and first.get("change_id") == second.get("change_id"):
                    links.append(CorrelationLink(correlation_id=f"change:{first_id}:{second_id}", correlation_type="change", source_ids=[first_id, second_id], strength="high", rationale="both records reference the same change", causal_claim=False))
        if not records:
            self.assumptions.append(Assumption("correlation_records", "not_supplied", "causal correlation cannot be inferred without evidence records", True))
        limitations = ["correlation is not proof of causation; causal_claim remains false"]
        decision = DecisionRecord("CorrelationEngine", "correlation-analysis", "non_causal_multi_source_correlation", "link evidence only on explicit temporal, spatial, or change metadata", ["non_causal_multi_source_correlation", "automatic_causal_attribution"], {"non_causal_multi_source_correlation": "selected", "automatic_causal_attribution": "rejected without proof"})
        self.decisions.append(decision)
        strength_order = {"none": 0, "low": 1, "medium": 2, "high": 3}
        strongest = max((item.strength for item in links), key=lambda value: strength_order.get(value, 0), default="none")
        return CorrelationReport(links=links, strongest_signal=strongest, confidence=min(0.8, 0.2 + (0.1 * len(links))) if links else 0.0, limitations=limitations, decision_id=decision.decision_id)

    @staticmethod
    def _time(value: Any) -> datetime | None:
        """Parse datetime values conservatively."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
