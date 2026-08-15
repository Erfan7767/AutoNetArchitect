"""Pydantic models for traceable troubleshooting evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .diagnostic_enums import CollectionMethod, EvidenceSource


class EvidenceRequest(BaseModel):
    """A request for one evidence item or read-only command."""

    model_config = ConfigDict(extra="forbid")

    evidence_type: str
    target_device: str = ""
    command_or_query: str = ""
    expected_data_type: str = "structured"
    timeout: float = 30.0
    required: bool = True
    rationale: str = ""

    def model_post_init(self, __context: Any) -> None:
        """Enforce positive timeout and read-only command policy."""
        if self.timeout <= 0:
            raise ValueError("evidence timeout must be positive")
        forbidden = ("configure", "set ", "delete ", "remove ", "reload", "restart", "shutdown", "write", "commit")
        if any(token in self.command_or_query.lower() for token in forbidden):
            raise ValueError("evidence requests may contain only read-only commands")


class EvidenceItem(BaseModel):
    """One collected evidence item with method and confidence metadata."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    source: EvidenceSource
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_data: Any = None
    parsed_data: dict[str, Any] = Field(default_factory=dict)
    collection_method: CollectionMethod
    confidence: float
    target_device: str = ""
    command_or_query: str = ""
    request_type: str = ""
    evidence_hash: str = ""
    notes: str = ""

    def model_post_init(self, __context: Any) -> None:
        """Validate confidence bounds and source/method consistency."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("evidence confidence must be between zero and one")
        if self.source == EvidenceSource.LIVE_COLLECTION and self.collection_method != CollectionMethod.LIVE_READ_ONLY:
            raise ValueError("live collection evidence must use live_read_only method")


class EvidenceCollection(BaseModel):
    """All evidence available to one diagnostic execution."""

    model_config = ConfigDict(extra="forbid")

    items: list[EvidenceItem] = Field(default_factory=list)
    requests: list[EvidenceRequest] = Field(default_factory=list)
    mode: str
    complete: bool = False
    missing_required: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)

    def by_id(self) -> dict[str, EvidenceItem]:
        """Index evidence items by their traceable identifier."""
        return {item.evidence_id: item for item in self.items}

    def parsed_values(self) -> dict[str, Any]:
        """Return parsed data keyed by evidence ID."""
        return {item.evidence_id: item.parsed_data for item in self.items}


class InterpretedEvidence(BaseModel):
    """Normalized evidence interpretation used by workflows."""

    model_config = ConfigDict(extra="forbid")

    facts: dict[str, Any] = Field(default_factory=dict)
    anomalies: list[str] = Field(default_factory=list)
    health_indicators: dict[str, str] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    limitations: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Validate interpretation confidence."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("interpreted evidence confidence must be between zero and one")
