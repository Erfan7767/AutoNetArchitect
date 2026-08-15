"""Pydantic models for final troubleshooting results and RCA."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .diagnostic_enums import DiagnosticStatus, RootCauseClassification, Severity
from .evidence_models import EvidenceItem
from .hypothesis_models import Hypothesis, HypothesisEvaluation
from .remediation_models import EscalationRecommendation, RemediationPlan
from .symptom_models import AffectedScope, SymptomClassification, SymptomInput


class DiagnosticTimelineEvent(BaseModel):
    """One event in the diagnostic timeline."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    description: str
    evidence_ids: list[str] = Field(default_factory=list)


class ImpactAssessment(BaseModel):
    """Observed or explicitly supplied impact assessment."""

    model_config = ConfigDict(extra="forbid")

    affected_scope: AffectedScope
    service_impact: str = "unknown"
    user_impact: str = "unknown"
    availability_impact: str = "unknown"
    security_impact: str = "unknown"
    confidence: float = 0.0
    assumptions: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Validate confidence."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("impact confidence must be between zero and one")


class RootCauseAnalysis(BaseModel):
    """Evidence-bounded root cause analysis."""

    model_config = ConfigDict(extra="forbid")

    root_cause: str
    root_cause_confidence: float
    contributing_factors: list[str] = Field(default_factory=list)
    evidence_supporting: list[EvidenceItem] = Field(default_factory=list)
    evidence_contradicting: list[EvidenceItem] = Field(default_factory=list)
    root_cause_classification: RootCauseClassification
    confidence_level: str
    unresolved_uncertainties: list[str] = Field(default_factory=list)
    tested_hypotheses: list[HypothesisEvaluation] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Validate root cause confidence and level consistency."""
        if not 0.0 <= self.root_cause_confidence <= 1.0:
            raise ValueError("root cause confidence must be between zero and one")
        if self.root_cause_confidence > 0.8 and self.confidence_level != "high":
            raise ValueError("confidence level must be high above 0.8")


class DiagnosticResult(BaseModel):
    """Complete auditable output of a troubleshooting session."""

    model_config = ConfigDict(extra="forbid")

    diagnostic_id: str
    status: DiagnosticStatus
    analysis_mode: str
    symptom_input: SymptomInput
    symptom_classification: SymptomClassification
    timeline: list[DiagnosticTimelineEvent] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    evidence_requests: list[Any] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    hypothesis_evaluations: list[HypothesisEvaluation] = Field(default_factory=list)
    root_cause_analysis: RootCauseAnalysis
    impact_assessment: ImpactAssessment
    remediation_plan: RemediationPlan
    escalation: EscalationRecommendation
    related_changes: list[Any] = Field(default_factory=list)
    known_issue_matches: list[Any] = Field(default_factory=list)
    packet_path: Any | None = None
    decision_records: list[Any] = Field(default_factory=list)
    assumptions: list[Any] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
