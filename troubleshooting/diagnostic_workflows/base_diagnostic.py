"""Base class for read-only diagnostic workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field

from ..hypothesis_engine import HypothesisEngine
from ..models import EvidenceCollection, Hypothesis, HypothesisEvaluation, InterpretedEvidence, VerificationStep


class DiagnosticDecisionTree(BaseModel):
    """Declarative decision tree metadata."""

    model_config = ConfigDict(extra="forbid")

    tree_id: str
    direction: str
    nodes: list[dict[str, Any]] = Field(default_factory=list)


class NextStep(BaseModel):
    """Suggested next read-only diagnostic step."""

    model_config = ConfigDict(extra="forbid")

    description: str
    commands: list[str] = Field(default_factory=list)
    rationale: str
    blocked: bool = False


class DiagnosticWorkflowOutput(BaseModel):
    """Workflow-specific diagnostic output."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    status: str
    findings: list[str] = Field(default_factory=list)
    interpreted_evidence: InterpretedEvidence
    hypothesis_evaluations: list[HypothesisEvaluation] = Field(default_factory=list)
    next_steps: list[NextStep] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class BaseDiagnostic(ABC):
    """Shared read-only workflow behavior and audit records."""

    diagnostic_id = "base_diagnostic"
    symptom_class = "unknown"
    required_evidence_types: tuple[str, ...] = ()
    decision_tree = DiagnosticDecisionTree(tree_id="base", direction="divide_and_conquer", nodes=[])

    def __init__(self) -> None:
        """Initialize workflow decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    @abstractmethod
    def execute(self, evidence: EvidenceCollection, hypotheses: Iterable[Hypothesis] = ()) -> DiagnosticWorkflowOutput:
        """Execute workflow against supplied evidence."""

    def get_required_commands(self, vendor: str, platform: str) -> list[str]:
        """Return safe vendor/platform commands from the workflow registry."""
        del vendor, platform
        return [f"show diagnostic evidence for {self.symptom_class}"]

    def interpret_evidence(self, evidence: EvidenceCollection) -> InterpretedEvidence:
        """Normalize evidence into facts, anomalies, and health indicators."""
        facts: dict[str, Any] = {}
        anomalies: list[str] = []
        indicators: dict[str, str] = {}
        ids: list[str] = []
        confidences: list[float] = []
        for item in evidence.items:
            ids.append(item.evidence_id)
            confidences.append(item.confidence)
            facts[item.evidence_id] = item.parsed_data
            text = f"{item.raw_data} {item.parsed_data}".lower()
            if any(token in text for token in ("down", "fail", "error", "deny", "blocked", "timeout", "crc", "drop", "mismatch")):
                anomalies.append(f"anomaly indicator present in {item.evidence_id}")
                indicators[item.evidence_id] = "degraded_or_failed"
            else:
                indicators[item.evidence_id] = "observed_without_bounded_anomaly"
        confidence = sum(confidences) / len(confidences) if confidences else 0.0
        limitations = list(evidence.missing_required)
        if not evidence.items:
            limitations.append("no evidence items were supplied")
        return InterpretedEvidence(facts=facts, anomalies=anomalies, health_indicators=indicators, evidence_ids=ids, confidence=confidence, limitations=limitations)

    def evaluate_hypothesis(self, hypothesis: Hypothesis, evidence: EvidenceCollection) -> HypothesisEvaluation:
        """Evaluate one hypothesis using the shared evidence engine."""
        return HypothesisEngine().evaluate(hypothesis, evidence)

    def suggest_next_step(self, current_state: InterpretedEvidence) -> NextStep:
        """Suggest a read-only next step when evidence is incomplete."""
        if current_state.limitations:
            return NextStep(description="collect the missing evidence types before asserting a root cause", commands=self.get_required_commands("", ""), rationale="available evidence is incomplete", blocked=True)
        return NextStep(description="perform the next workflow-specific read-only verification", commands=self.get_required_commands("", ""), rationale="workflow evidence remains bounded", blocked=False)

    def _build_output(self, evidence: EvidenceCollection, hypotheses: Iterable[Hypothesis], findings: list[str]) -> DiagnosticWorkflowOutput:
        """Build common workflow output and record the workflow decision."""
        interpreted = self.interpret_evidence(evidence)
        evaluations = [self.evaluate_hypothesis(hypothesis, evidence) for hypothesis in hypotheses]
        next_step = self.suggest_next_step(interpreted)
        status = "completed" if evidence.complete else "partially_completed"
        self.decisions.append(DecisionRecord(self.__class__.__name__, f"workflow:{self.diagnostic_id}", status, "execute read-only workflow and preserve missing-evidence limitations", ["completed", "partially_completed", "blocked"], {"completed": "all required evidence available", "partially_completed": "some evidence available", "blocked": "no safe evidence path"}))
        return DiagnosticWorkflowOutput(workflow_id=self.diagnostic_id, status=status, findings=findings, interpreted_evidence=interpreted, hypothesis_evaluations=evaluations, next_steps=[next_step], evidence_ids=interpreted.evidence_ids, assumptions=list(dict.fromkeys(evidence.assumptions + [item.key for item in self.assumptions])))
