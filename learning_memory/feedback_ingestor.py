"""Ingestion of human and operational feedback into learning memory."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .discrepancy_registry import ActualOutcome, DiscrepancyRecord, DiscrepancyRegistry, DiscrepancySeverity, DiscrepancyType, HumanCorrection
from .failure_memory import FailureMemory, FailureMemoryEntry


class FeedbackSource(str, Enum):
    """Accepted feedback channels."""

    HUMAN_REVIEW = "human_review"
    LAB_FINDING = "lab_finding"
    DEPLOYMENT_FINDING = "deployment_finding"
    OPERATIONAL_FINDING = "operational_finding"


class FeedbackRecord(BaseModel):
    """One feedback finding with enough context to become durable memory."""

    model_config = ConfigDict(extra="forbid")

    feedback_id: str = Field(min_length=1)
    source: FeedbackSource
    scenario_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    discrepancy_type: DiscrepancyType
    severity: DiscrepancySeverity = DiscrepancySeverity.MEDIUM
    proposed_value: Any = None
    evidence_state: str = Field(min_length=1)
    evidence_ids: tuple[str, ...] = ()
    actual_outcome: ActualOutcome
    human_correction: HumanCorrection | None = None
    failure_reference: str = ""


class IngestedFeedback(BaseModel):
    """Links created by feedback ingestion."""

    model_config = ConfigDict(extra="forbid")

    feedback_id: str
    discrepancy_id: str
    failure_id: str
    source: FeedbackSource
    evidence_ids: tuple[str, ...] = ()


class FeedbackIngestor(BaseDesigner):
    """Convert feedback into discrepancy and failure memory records."""

    def __init__(self, *, discrepancy_registry: DiscrepancyRegistry | None = None, failure_memory: FailureMemory | None = None) -> None:
        """Initialize feedback ingestion with durable registries."""
        super().__init__("FeedbackIngestor")
        self.discrepancy_registry = discrepancy_registry or DiscrepancyRegistry()
        self.failure_memory = failure_memory or FailureMemory()
        self.record_decision("feedback_ingestion_policy", "all_supported_sources_retained", "human, lab, deployment, and operational findings become linked memory")

    def ingest(self, feedback: FeedbackRecord) -> IngestedFeedback:
        """Ingest one feedback record without dropping its source or evidence."""
        discrepancy = DiscrepancyRecord(discrepancy_id=f"discrepancy:{feedback.feedback_id}", discrepancy_type=feedback.discrepancy_type, severity=feedback.severity, scenario_id=feedback.scenario_id, decision_id=feedback.decision_id, proposed_value=feedback.proposed_value, evidence_state=feedback.evidence_state, evidence_ids=feedback.evidence_ids, actual_outcome=feedback.actual_outcome, human_correction=feedback.human_correction, failure_reference=feedback.failure_reference)
        self.discrepancy_registry.record(discrepancy)
        failure = self.failure_memory.record(discrepancy, failure_id=f"failure:{feedback.feedback_id}")
        self.record_decision(f"feedback:{feedback.feedback_id}", feedback.source.value, "feedback was normalized into discrepancy and failure memory")
        return IngestedFeedback(feedback_id=feedback.feedback_id, discrepancy_id=discrepancy.discrepancy_id, failure_id=failure.failure_id, source=feedback.source, evidence_ids=tuple(dict.fromkeys(feedback.evidence_ids + feedback.actual_outcome.evidence_ids)))
