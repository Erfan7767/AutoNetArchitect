"""Escalation recommendations for unresolved or high-impact incidents."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Mapping

from designers.base_designer import Assumption, DecisionRecord

from .models import EscalationRecommendation, EscalationTarget, RootCauseAnalysis, Severity, SymptomInput


class EscalationAdvisor:
    """Determine escalation needs without creating external tickets automatically."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def advise(self, symptom: SymptomInput, rca: RootCauseAnalysis, *, duration_hours: float | None = None, critical_service: bool = False, impact_exceeds_team: bool = False) -> EscalationRecommendation:
        """Evaluate escalation criteria explicitly supplied by the caller."""
        reasons: list[str] = []
        targets: list[EscalationTarget] = []
        checks: dict[str, bool] = {}
        low_confidence = rca.root_cause_confidence < 0.3
        checks["low_confidence"] = low_confidence
        if low_confidence:
            reasons.append("root cause confidence is below 0.3 after available local analysis")
            targets.append(EscalationTarget.SPECIALIZED_ENGINEERING)
        hardware = rca.root_cause_classification.value == "hardware_failure"
        checks["suspected_hardware_failure"] = hardware
        if hardware:
            reasons.append("suspected hardware failure requires field or hardware support")
            targets.append(EscalationTarget.FIELD_SUPPORT)
        software = rca.root_cause_classification.value == "software_bug"
        checks["suspected_software_bug"] = software
        if software:
            reasons.append("suspected software bug requires vendor engagement")
            targets.append(EscalationTarget.VENDOR_TAC)
        security = rca.root_cause_classification.value == "security_incident"
        checks["suspected_security_incident"] = security
        if security:
            reasons.append("suspected security incident requires security-team handling")
            targets.append(EscalationTarget.SECURITY_TEAM)
        checks["impact_exceeds_team"] = impact_exceeds_team
        if impact_exceeds_team:
            reasons.append("reported impact exceeds the current team scope")
            targets.append(EscalationTarget.SPECIALIZED_ENGINEERING)
        duration_breach = duration_hours is not None and duration_hours > self._sla_hours(symptom.severity)
        checks["sla_breached"] = duration_breach
        if duration_breach:
            reasons.append("issue duration exceeds the bounded severity SLA threshold")
            targets.append(EscalationTarget.MANAGEMENT)
        checks["critical_service"] = critical_service
        if critical_service:
            reasons.append("critical service impact was explicitly supplied")
            targets.append(EscalationTarget.MANAGEMENT)
        if duration_hours is None:
            self.assumptions.append(Assumption("issue_duration", "unknown", "SLA breach cannot be inferred without an explicit duration", True))
        required = bool(reasons)
        self.decisions.append(DecisionRecord("EscalationAdvisor", "escalation-evaluation", required, "escalate only for explicit low-confidence, risk, scope, SLA, or service criteria", [True, False], {"True": "one or more criteria met", "False": "no supplied criterion met"}))
        return EscalationRecommendation(required=required, targets=list(dict.fromkeys(targets)), reasons=list(dict.fromkeys(reasons)), threshold_evaluations=checks, package_contents=["diagnostic report", "evidence collected", "steps already taken", "impact assessment"], urgency="critical" if symptom.severity == Severity.CRITICAL else "high" if symptom.severity == Severity.HIGH else "normal")

    @staticmethod
    def _sla_hours(severity: Severity) -> float:
        """Return bounded default SLA thresholds, clearly marked as policy defaults."""
        return {Severity.CRITICAL: 1.0, Severity.HIGH: 4.0, Severity.MEDIUM: 24.0, Severity.LOW: 72.0}[severity]
