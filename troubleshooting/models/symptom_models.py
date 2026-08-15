"""Pydantic models for incident scope and symptom classification."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .diagnostic_enums import AffectedScopeType, Severity, SymptomClass


class AffectedScope(BaseModel):
    """Explicit scope of the reported issue."""

    model_config = ConfigDict(extra="forbid")

    scope_type: AffectedScopeType
    identifiers: list[str] = Field(default_factory=list)
    site_id: str | None = None
    service_id: str | None = None
    description: str = ""


class SymptomInput(BaseModel):
    """Input contract for a troubleshooting session."""

    model_config = ConfigDict(extra="forbid")

    symptom_description: str
    affected_scope: AffectedScope
    severity: Severity
    reported_by: str
    reported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    additional_context: dict[str, Any] = Field(default_factory=dict)


class SymptomClassification(BaseModel):
    """Evidence-bounded classification of reported symptoms."""

    model_config = ConfigDict(extra="forbid")

    primary_class: SymptomClass
    secondary_classes: list[SymptomClass] = Field(default_factory=list)
    subtype: str = "unknown"
    confidence: float = 0.0
    rationale: str
    suggested_diagnostic_workflows: list[str] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    decision_id: str

    def model_post_init(self, __context: Any) -> None:
        """Validate confidence bounds after Pydantic initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("symptom classification confidence must be between zero and one")
