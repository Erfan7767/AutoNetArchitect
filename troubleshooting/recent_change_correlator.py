"""Correlate recent change history with reported troubleshooting scope."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field

from .models import AffectedScope


class PotentiallyRelatedChange(BaseModel):
    """One recent change that may be related to the incident."""

    model_config = ConfigDict(extra="forbid")

    change_id: str
    title: str = ""
    changed_at: datetime | None = None
    affected_devices: list[str] = Field(default_factory=list)
    affected_sites: list[str] = Field(default_factory=list)
    feature_area: str = ""
    correlation_strength: str
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)


class RecentChangeCorrelator:
    """Search only supplied change history within an explicit time window."""

    def __init__(self) -> None:
        """Initialize audit registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def correlate(self, affected_scope: AffectedScope, changes: Iterable[Mapping[str, Any]], *, now: datetime | None = None, hours: int = 72, feature_area: str = "") -> list[PotentiallyRelatedChange]:
        """Return recent changes with explicit scope and feature correlations."""
        current = now or datetime.now(timezone.utc)
        cutoff = current - timedelta(hours=hours)
        identifiers = set(affected_scope.identifiers)
        results: list[PotentiallyRelatedChange] = []
        for raw in changes:
            item = dict(raw)
            changed_at = self._parse_time(item.get("changed_at", item.get("timestamp")))
            if changed_at is not None and changed_at < cutoff:
                continue
            devices = [str(value) for value in item.get("affected_devices", [])]
            sites = [str(value) for value in item.get("affected_sites", [])]
            area = str(item.get("feature_area", ""))
            same_device = bool(identifiers.intersection(devices))
            same_site = bool(affected_scope.site_id and affected_scope.site_id in sites)
            same_feature = bool(feature_area and area and feature_area.lower() == area.lower())
            if same_device and same_feature:
                strength, rationale = "high", "same device and same feature area"
            elif same_device:
                strength, rationale = "medium", "same device with a different or unspecified feature area"
            elif same_site and same_feature:
                strength, rationale = "medium", "same site and same feature area"
            elif same_site:
                strength, rationale = "low", "same site with a different or unspecified feature area"
            else:
                continue
            results.append(PotentiallyRelatedChange(change_id=str(item.get("change_id", "unknown-change")), title=str(item.get("title", "")), changed_at=changed_at, affected_devices=devices, affected_sites=sites, feature_area=area, correlation_strength=strength, rationale=rationale, evidence_ids=[str(value) for value in item.get("evidence_ids", [])]))
        if not changes:
            self.assumptions.append(Assumption("change_history", "not_supplied", "recent change correlation cannot be inferred without change history", True))
        self.decisions.append(DecisionRecord("RecentChangeCorrelator", "recent-change-correlation", "scope_and_time_bounded", "consider only supplied changes inside the configured time window", ["scope_and_time_bounded", "all_history"], {"scope_and_time_bounded": "selected", "all_history": "rejected because it obscures recency"}))
        return sorted(results, key=lambda item: {"high": 0, "medium": 1, "low": 2}.get(item.correlation_strength, 3))

    @staticmethod
    def _parse_time(value: Any) -> datetime | None:
        """Parse explicit timestamps only."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
