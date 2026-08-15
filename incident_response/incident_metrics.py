"""Incident management metrics from explicit incident records."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Sequence

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field

from ._common import make_assumption, make_decision
from .incident_models import Incident


class IncidentMetrics(BaseModel):
    """Aggregated incident metrics with missing-data limitations."""

    model_config = ConfigDict(extra="forbid")

    period_start: datetime | None = None
    period_end: datetime | None = None
    total_incidents: int
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    by_site: dict[str, int] = Field(default_factory=dict)
    mttd: timedelta | None = None
    mtta: timedelta | None = None
    mttr: timedelta | None = None
    mtbf_by_device: dict[str, timedelta] = Field(default_factory=dict)
    change_failure_rate: float | None = None
    recurring_incidents: int = 0
    reopened_incidents: int = 0
    sla_compliance_rate: float | None = None
    escalation_rate: float | None = None
    false_alarm_rate: float | None = None
    trend: str = "insufficient_data"
    assumptions: list[str] = Field(default_factory=list)
    decision_id: str


class IncidentMetricsCalculator:
    """Calculate transparent metrics without treating missing timestamps as zero."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def calculate(self, incidents: Sequence[Incident], *, period_start: datetime | None = None, period_end: datetime | None = None) -> IncidentMetrics:
        """Aggregate incident records and record limitations."""
        values = list(incidents)
        if not values:
            self.assumptions.append(make_assumption("metrics:incidents", "none", "metrics cannot be inferred without incident records", True))
        severities = Counter(item.severity.value for item in values)
        categories = Counter(item.category.value for item in values)
        sites = Counter(site for item in values for site in item.affected_sites)
        detection_times = [item.detected_at for item in values if item.detected_at]
        response = [(item.acknowledged_at - item.detected_at) for item in values if item.acknowledged_at is not None]
        resolution = [(item.resolved_at - item.detected_at) for item in values if item.resolved_at is not None]
        if len(response) < len(values):
            self.assumptions.append(make_assumption("metrics:mtta", "partial", "MTTA excludes incidents without acknowledgment timestamps", True))
        if len(resolution) < len(values):
            self.assumptions.append(make_assumption("metrics:mttr", "partial", "MTTR excludes ongoing incidents without resolution timestamps", True))
        related_change_count = sum(bool(item.related_changes) for item in values)
        resolved_count = sum(item.resolved_at is not None for item in values)
        escalated_count = sum(item.escalation_level > 0 for item in values)
        reopened_count = sum(1 for item in values if item.status.value == "monitoring")
        decision = make_decision("IncidentMetricsCalculator", "incident-metrics", "explicit_timestamp_aggregation", "calculate only from supplied timestamps and incident metadata", ["explicit_timestamp_aggregation", "zero_fill_missing_values"], {"explicit_timestamp_aggregation": "selected", "zero_fill_missing_values": "rejected"})
        self.decisions.append(decision)
        return IncidentMetrics(period_start=period_start, period_end=period_end, total_incidents=len(values), by_severity=dict(severities), by_category=dict(categories), by_site=dict(sites), mttd=None, mtta=self._average(response), mttr=self._average(resolution), change_failure_rate=related_change_count / len(values) if values else None, recurring_incidents=0, reopened_incidents=reopened_count, sla_compliance_rate=None, escalation_rate=escalated_count / len(values) if values else None, false_alarm_rate=None, trend="insufficient_data" if len(values) < 2 else "stable_pending_period_comparison", assumptions=[item.key for item in self.assumptions], decision_id=decision.decision_id)

    @staticmethod
    def _average(values: Sequence[timedelta]) -> timedelta | None:
        """Average duration, preserving None for empty data."""
        return sum(values, timedelta(0)) / len(values) if values else None
