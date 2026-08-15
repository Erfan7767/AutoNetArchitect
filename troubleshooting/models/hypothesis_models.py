"""Pydantic models for diagnostic hypotheses and verification steps."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VerificationStep(BaseModel):
    """One read-only step used to test a hypothesis."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    description: str
    commands: list[str] = Field(default_factory=list)
    expected_pattern: str = ""
    interpretation: str = ""
    read_only: bool = True
    order: int = 0

    def model_post_init(self, __context: Any) -> None:
        """Reject commands that are not explicitly read-only."""
        if not self.read_only:
            raise ValueError("diagnostic verification steps must be read-only")
        forbidden = ("configure", "set ", "delete ", "remove ", "reload", "restart", "shutdown", "write", "commit", "execute")
        if any(any(token in command.lower() for token in forbidden) for command in self.commands):
            raise ValueError("verification steps may contain only read-only commands")


class Hypothesis(BaseModel):
    """A possible cause ordered by evidence-bounded probability."""

    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str
    description: str
    probability_score: float
    verification_steps: list[VerificationStep] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    affects_layer: str
    typical_resolution: str
    source: str = "bounded_hypothesis_library"
    rationale: str = ""

    def model_post_init(self, __context: Any) -> None:
        """Validate probability bounds."""
        if not 0.0 <= self.probability_score <= 1.0:
            raise ValueError("hypothesis probability must be between zero and one")


class HypothesisEvaluation(BaseModel):
    """Result of testing one hypothesis against available evidence."""

    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str
    status: str
    support_score: float
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    rationale: str
    confidence: float

    def model_post_init(self, __context: Any) -> None:
        """Validate scores."""
        if not 0.0 <= self.support_score <= 1.0 or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("hypothesis scores must be between zero and one")
