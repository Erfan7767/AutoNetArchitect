"""Incident correlation and duplicate suppression recommendations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field

from ._common import make_assumption, make_decision
from .incident_models import Incident


class IncidentCorrelation(BaseModel):
    """One relationship between incidents."""

    model_config = ConfigDict(extra="forbid")

    correlation_id: str
    correlation_type: str
    parent_incident_id: str
    child_incident_ids: list[str] = Field(default_factory=list)
    strength: str
    rationale: str
    suppress_child_alerts_recommended: bool = False
    causal_claim_verified: bool = False
    evidence_ids: list[str] = Field(default_factory=list)


class IncidentCorrelationEngine:
    """Correlate incidents without silently merging or suppressing them."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def correlate(self, incidents: Sequence[Incident], *, window_seconds: int = 300) -> list[IncidentCorrelation]:
        """Return candidate relationships from explicit time, scope, and path signals."""
        results: list[IncidentCorrelation] = []
        ordered = sorted(incidents, key=lambda item: item.detected_at)
        for index, parent in enumerate(ordered):
            for child in ordered[index + 1:]:
                same_time = abs((child.detected_at - parent.detected_at).total_seconds()) <= window_seconds
                same_devices = bool(set(parent.affected_devices).intersection(child.affected_devices))
                same_services = bool(set(parent.affected_services).intersection(child.affected_services))
                same_sites = bool(set(parent.affected_sites).intersection(child.affected_sites))
                if parent.title.strip().lower() == child.title.strip().lower() and same_time:
                    results.append(IncidentCorrelation(correlation_id=f"duplicate:{parent.incident_id}:{child.incident_id}", correlation_type="duplicate", parent_incident_id=parent.incident_id, child_incident_ids=[child.incident_id], strength="high", rationale="same title and close detection time", suppress_child_alerts_recommended=True))
                elif same_time and (same_devices or same_services):
                    results.append(IncidentCorrelation(correlation_id=f"temporal:{parent.incident_id}:{child.incident_id}", correlation_type="temporal_and_scope", parent_incident_id=parent.incident_id, child_incident_ids=[child.incident_id], strength="medium", rationale="incidents overlap in time and explicit device/service scope", suppress_child_alerts_recommended=False))
                elif same_sites and same_time:
                    results.append(IncidentCorrelation(correlation_id=f"site:{parent.incident_id}:{child.incident_id}", correlation_type="topological_or_site", parent_incident_id=parent.incident_id, child_incident_ids=[child.incident_id], strength="low", rationale="incidents share site and time but causal relation is unverified", suppress_child_alerts_recommended=False))
        if not incidents:
            self.assumptions.append(make_assumption("incident_correlation:input", "not_supplied", "correlation cannot be inferred without incident records", True))
        self.decisions.append(make_decision("IncidentCorrelationEngine", "incident-correlation", "recommend_relationships_only", "candidate relationships are reported without automatic merge, suppression, or causal assertion", ["recommend_relationships_only", "automatic_merge_and_suppression"], {"recommend_relationships_only": "selected", "automatic_merge_and_suppression": "rejected"}))
        return results
