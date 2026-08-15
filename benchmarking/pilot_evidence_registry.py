"""Registry for evidence from real pilot environments."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner


class PilotStatus(str, Enum):
    """Pilot evidence lifecycle."""

    CAPTURED = "captured"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    VALIDATED = "validated"
    EXCLUDED = "excluded"


class PilotEvidenceRecord(BaseModel):
    """Bounded evidence record from a real pilot environment."""

    model_config = ConfigDict(extra="forbid")

    pilot_id: str = Field(min_length=1)
    environment_name: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    scenario_ids: tuple[str, ...] = ()
    metric_results: tuple[dict, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    human_review_reference: str = ""
    limitations: tuple[str, ...] = ()
    status: PilotStatus = PilotStatus.CAPTURED
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PilotEvidenceRegistry(BaseDesigner):
    """Retain pilot evidence and prevent unreviewed records from becoming claims."""

    def __init__(self) -> None:
        """Initialize registry."""
        super().__init__("PilotEvidenceRegistry")
        self._records: dict[str, PilotEvidenceRecord] = {}
        self.record_decision("pilot_evidence_policy", "human_validation_required", "pilot evidence remains scoped and limited until human review validates it")

    def register(self, record: PilotEvidenceRecord) -> PilotEvidenceRecord:
        """Register one pilot record without replacing an existing one."""
        if record.pilot_id in self._records:
            raise ValueError(f"pilot evidence already exists: {record.pilot_id}")
        self._records[record.pilot_id] = record
        return record

    def validate(self, pilot_id: str, *, human_review_reference: str, limitations: Iterable[str] = ()) -> PilotEvidenceRecord:
        """Mark pilot evidence validated only with reviewer reference and limitations."""
        if not human_review_reference.strip():
            raise ValueError("human_review_reference is mandatory")
        current = self._records[pilot_id]
        updated = current.model_copy(update={"status": PilotStatus.VALIDATED, "human_review_reference": human_review_reference, "limitations": tuple(dict.fromkeys(current.limitations + tuple(str(item) for item in limitations)))})
        self._records[pilot_id] = updated
        self.record_decision(f"pilot_validate:{pilot_id}", PilotStatus.VALIDATED.value, "pilot evidence was human reviewed within declared scope")
        return updated

    def usable(self) -> tuple[PilotEvidenceRecord, ...]:
        """Return only validated pilot evidence."""
        return tuple(item for item in self._records.values() if item.status == PilotStatus.VALIDATED)

    def all(self) -> tuple[PilotEvidenceRecord, ...]:
        """Return all pilot evidence records."""
        return tuple(self._records.values())
