"""Incident escalation decisions and handoff artifacts."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Sequence

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field

from ._common import make_assumption, make_decision
from .incident_models import Incident, IncidentSeverity


class EscalationDecision(BaseModel):
    """Escalation result with target, authority, and war-room decision."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str
    level: int
    targets: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    expected_response: timedelta
    authority_level: str
    war_room_required: bool
    handoff_package: list[str] = Field(default_factory=list)
    decision_id: str
    assumptions: list[str] = Field(default_factory=list)


class EscalationEngine:
    """Apply explicit severity, scope, time, and complexity escalation rules."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def evaluate(self, incident: Incident, *, elapsed: timedelta | None = None, scope_spreading: bool = False, diagnosis_exceeds_team: bool = False, current_level: int | None = None) -> EscalationDecision:
        """Return the next escalation level without sending notifications."""
        level = current_level if current_level is not None else incident.escalation_level
        reasons: list[str] = []
        if incident.severity == IncidentSeverity.P1_CRITICAL:
            level = max(level, 4)
            reasons.append("P1 critical incident requires immediate management escalation")
        elif incident.severity == IncidentSeverity.P2_HIGH:
            level = max(level, 2)
            reasons.append("P2 high incident requires senior engineering ownership")
        elif incident.severity == IncidentSeverity.P3_MEDIUM:
            level = max(level, 1)
            reasons.append("P3 medium incident requires on-call ownership and time-based review")
        else:
            level = max(level, 1)
            reasons.append("P4 low incident remains at on-call level unless SLA or scope changes")
        if scope_spreading:
            level = min(4, level + 1)
            reasons.append("impact is explicitly spreading across additional scope")
        if diagnosis_exceeds_team:
            level = min(4, level + 1)
            reasons.append("diagnosis exceeds the current team capability")
        if elapsed is not None and elapsed >= self._escalation_after(incident.severity):
            level = min(4, level + 1)
            reasons.append("explicit elapsed time crossed the severity escalation threshold")
        else:
            self.assumptions.append(make_assumption(f"{incident.incident_id}:escalation_time", "unknown" if elapsed is None else elapsed.total_seconds(), "time-based escalation is not inferred without an explicit elapsed duration", True))
        targets = {1: ["on_call_engineer"], 2: ["senior_engineer", "team_lead"], 3: ["architecture_team", "vendor_tac"], 4: ["management", "cto"]}[level]
        authority = {1: "observe_and_collect", 2: "coordinate_and_approve_standard_governance", 3: "authorize_specialist_or_vendor_review", 4: "authorize_business_continuity_and_major_risk_decisions"}[level]
        response = {1: timedelta(minutes=30), 2: timedelta(minutes=30), 3: timedelta(minutes=15), 4: timedelta(minutes=15)}[level]
        decision = make_decision("EscalationEngine", f"{incident.incident_id}:escalation:{level}", level, "choose the lowest level that satisfies explicit severity, scope, time, and capability criteria", [1, 2, 3, 4], {str(item): "not selected by current evidence" for item in [1, 2, 3, 4] if item != level})
        self.decisions.append(decision)
        return EscalationDecision(incident_id=incident.incident_id, level=level, targets=targets, reasons=list(dict.fromkeys(reasons)), expected_response=response, authority_level=authority, war_room_required=incident.severity == IncidentSeverity.P1_CRITICAL, handoff_package=["incident record", "timeline", "evidence references", "diagnosis or current hypotheses", "impact assessment", "approved or pending plans"], decision_id=decision.decision_id, assumptions=[item.key for item in self.assumptions])

    @staticmethod
    def _escalation_after(severity: IncidentSeverity) -> timedelta:
        """Return the policy threshold before another escalation."""
        return {IncidentSeverity.P1_CRITICAL: timedelta(0), IncidentSeverity.P2_HIGH: timedelta(hours=1), IncidentSeverity.P3_MEDIUM: timedelta(hours=4), IncidentSeverity.P4_LOW: timedelta(hours=24)}[severity]
