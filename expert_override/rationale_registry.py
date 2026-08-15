"""Registry for human engineering rationale."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner


class EngineeringRationale(BaseModel):
    """Human rationale attached to an intervention."""

    model_config = ConfigDict(extra="forbid")

    rationale_id: str = Field(min_length=1)
    override_id: str = Field(min_length=1)
    author_id: str = Field(min_length=1)
    author_role: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    technical_basis: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    accepted_assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    requires_revalidation: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RationaleRegistry(BaseDesigner):
    """Store rationale records without replacing machine rationale."""

    def __init__(self) -> None:
        """Initialize an empty rationale registry."""
        super().__init__("RationaleRegistry")
        self._records: dict[str, EngineeringRationale] = {}
        self.record_decision("rationale_policy", "human_statement_retained", "human engineering rationale is additive provenance and cannot erase machine evidence")

    def register(self, rationale: EngineeringRationale) -> EngineeringRationale:
        """Register one rationale and reject duplicate identifiers."""
        if rationale.rationale_id in self._records:
            raise ValueError(f"rationale already exists: {rationale.rationale_id}")
        self._records[rationale.rationale_id] = rationale
        self.record_decision(f"rationale:{rationale.rationale_id}", "registered", "human rationale is retained as a separate provenance record")
        return rationale

    def get(self, rationale_id: str) -> EngineeringRationale:
        """Return one rationale record."""
        return self._records[rationale_id]

    def for_override(self, override_id: str) -> tuple[EngineeringRationale, ...]:
        """Return all rationale records for an override."""
        return tuple(item for item in self._records.values() if item.override_id == override_id)

    def all(self) -> tuple[EngineeringRationale, ...]:
        """Return rationale records in stable order."""
        return tuple(self._records[key] for key in sorted(self._records))
