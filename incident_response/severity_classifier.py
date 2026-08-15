"""Evidence-bounded incident severity classification."""

from __future__ import annotations

from typing import Any, Mapping

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field

from ._common import make_assumption, make_decision
from .incident_models import IncidentPriority, IncidentSeverity


class SeverityClassification(BaseModel):
    """Severity result with scoring rationale and governance metadata."""

    model_config = ConfigDict(extra="forbid")

    severity: IncidentSeverity
    priority: IncidentPriority
    score: float
    rationale: str
    factors: dict[str, Any] = Field(default_factory=dict)
    human_override_applied: bool = False
    decision_id: str
    assumptions: list[str] = Field(default_factory=list)


class SeverityClassifier:
    """Classify incidents conservatively and expose every factor used."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def classify(self, *, affected_users: int | None, service_criticality: str, business_impact: str, business_hours: bool | None, workaround_available: bool | None, duration_expected_minutes: int | None, sector: str = "", human_override: IncidentSeverity | str | None = None) -> SeverityClassification:
        """Return a severity classification from explicit signals only."""
        factors: dict[str, Any] = {"affected_users": affected_users, "service_criticality": service_criticality, "business_impact": business_impact, "business_hours": business_hours, "workaround_available": workaround_available, "duration_expected_minutes": duration_expected_minutes, "sector": sector}
        missing: list[str] = []
        if affected_users is None:
            missing.append("affected_users")
        if business_hours is None:
            missing.append("business_hours")
        if workaround_available is None:
            missing.append("workaround_available")
        if duration_expected_minutes is None:
            missing.append("duration_expected_minutes")
        if missing:
            for key in missing:
                self.assumptions.append(make_assumption(f"severity:{key}", "unknown", "severity factor was not supplied and is not inferred", True))
        critical_service = service_criticality.lower() in {"critical", "core", "clinical", "core_banking", "banking_core"}
        important_service = service_criticality.lower() in {"important", "high", "essential"}
        users = affected_users if affected_users is not None else 0
        impact_critical = business_impact.lower() in {"critical", "severe", "major", "outage"}
        if sector.lower() == "banking" and (critical_service or "core" in service_criticality.lower()):
            severity = IncidentSeverity.P1_CRITICAL
            rationale = "banking sector override: explicit core banking or critical-service impact requires P1 review"
        elif sector.lower() in {"hospital", "hospital_clinical", "healthcare"} and service_criticality.lower() in {"clinical", "critical"}:
            severity = IncidentSeverity.P1_CRITICAL
            rationale = "hospital sector override: explicit clinical-critical impact requires P1 review"
        elif (users > 1000 and critical_service) or impact_critical:
            severity = IncidentSeverity.P1_CRITICAL
            rationale = "large user impact or critical business impact crossed the P1 threshold"
        elif users > 100 or important_service:
            severity = IncidentSeverity.P2_HIGH
            rationale = "major user impact or important service crossed the P2 threshold"
        elif users > 10 or service_criticality.lower() in {"standard", "normal"}:
            severity = IncidentSeverity.P3_MEDIUM
            rationale = "limited but material impact crossed the P3 threshold"
        else:
            severity = IncidentSeverity.P4_LOW
            rationale = "small or non-critical impact remains within P4 threshold"
        override_applied = False
        if human_override is not None:
            override = IncidentSeverity(human_override)
            if self._rank(override) < self._rank(severity) or self._rank(override) > self._rank(severity):
                override_applied = True
                rationale = f"human override selected {override.value}; automatic result was {severity.value}"
                severity = override
        priority = {IncidentSeverity.P1_CRITICAL: IncidentPriority.CRITICAL, IncidentSeverity.P2_HIGH: IncidentPriority.HIGH, IncidentSeverity.P3_MEDIUM: IncidentPriority.MEDIUM, IncidentSeverity.P4_LOW: IncidentPriority.LOW}[severity]
        score = {IncidentSeverity.P1_CRITICAL: 1.0, IncidentSeverity.P2_HIGH: 0.75, IncidentSeverity.P3_MEDIUM: 0.5, IncidentSeverity.P4_LOW: 0.25}[severity]
        decision = make_decision("SeverityClassifier", f"severity:{severity.value}", severity.value, rationale, [item.value for item in IncidentSeverity], {item.value: "not selected by supplied factors or override" for item in IncidentSeverity if item != severity})
        self.decisions.append(decision)
        return SeverityClassification(severity=severity, priority=priority, score=score, rationale=rationale, factors=factors, human_override_applied=override_applied, decision_id=decision.decision_id, assumptions=[item.key for item in self.assumptions])

    @staticmethod
    def _rank(value: IncidentSeverity) -> int:
        """Return criticality rank where one is most severe."""
        return {IncidentSeverity.P1_CRITICAL: 1, IncidentSeverity.P2_HIGH: 2, IncidentSeverity.P3_MEDIUM: 3, IncidentSeverity.P4_LOW: 4}[value]
