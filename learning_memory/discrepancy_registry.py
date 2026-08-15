"""Registry for discrepancies between system proposals and observed reality."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner


class DiscrepancyType(str, Enum):
    """Supported discrepancy and failure-memory categories."""

    DESIGN_MISMATCH = "design_mismatch"
    EQUIPMENT_MISMATCH = "equipment_mismatch"
    CONFIG_MISMATCH = "config_mismatch"
    DEPLOYMENT_MISMATCH = "deployment_mismatch"
    FIELD_REALITY_MISMATCH = "field_reality_mismatch"
    UNSUPPORTED_CLAIM_INCIDENT = "unsupported_claim_incident"
    FALSE_CONFIDENCE_INCIDENT = "false_confidence_incident"


class DiscrepancySeverity(str, Enum):
    """Impact severity of a discrepancy."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActualOutcome(BaseModel):
    """Observed outcome retained separately from the proposed decision."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = Field(min_length=1)
    evidence_ids: tuple[str, ...] = ()
    impact: str = "unknown"
    raw_reference: str = ""


class HumanCorrection(BaseModel):
    """Explicit human correction applied after a discrepancy."""

    model_config = ConfigDict(extra="forbid")

    correction_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    actor_role: str = Field(min_length=1)
    action: str = Field(min_length=1)
    corrected_value: Any = None
    rationale: str = Field(min_length=1)
    decision_reference: str = ""
    evidence_ids: tuple[str, ...] = ()
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revalidation_required: bool = True


class DiscrepancyRecord(BaseModel):
    """A traceable mismatch linking proposal, evidence, outcome, and correction."""

    model_config = ConfigDict(extra="forbid")

    discrepancy_id: str = Field(min_length=1)
    discrepancy_type: DiscrepancyType
    severity: DiscrepancySeverity = DiscrepancySeverity.MEDIUM
    scenario_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    proposed_value: Any = None
    evidence_state: str = Field(min_length=1)
    evidence_ids: tuple[str, ...] = ()
    actual_outcome: ActualOutcome
    human_correction: HumanCorrection | None = None
    recurring_pattern_key: str = ""
    failure_reference: str = ""
    incident_reference: str = ""
    status: str = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: datetime | None = None


class DiscrepancyRegistry(BaseDesigner):
    """Append-oriented registry for discrepancies and mismatches."""

    def __init__(self) -> None:
        """Initialize discrepancy registry."""
        super().__init__("DiscrepancyRegistry")
        self._records: dict[str, DiscrepancyRecord] = {}
        self.record_decision("discrepancy_policy", "retain_failure_as_knowledge", "every discrepancy remains queryable and is not discarded as a transient warning")

    def record(self, record: DiscrepancyRecord) -> DiscrepancyRecord:
        """Record one discrepancy and reject identifier replacement."""
        if record.discrepancy_id in self._records:
            raise ValueError(f"discrepancy already exists: {record.discrepancy_id}")
        self._records[record.discrepancy_id] = record
        self.record_decision(f"discrepancy:{record.discrepancy_id}", record.discrepancy_type.value, "proposal and actual outcome were retained together")
        return record

    def attach_correction(self, discrepancy_id: str, correction: HumanCorrection) -> DiscrepancyRecord:
        """Attach explicit human correction without deleting the original outcome."""
        current = self._records[discrepancy_id]
        updated = current.model_copy(update={"human_correction": correction, "status": "corrected"})
        self._records[discrepancy_id] = updated
        self.record_decision(f"correction:{discrepancy_id}", correction.action, "human correction was attached while preserving the original mismatch")
        return updated

    def close(self, discrepancy_id: str, *, closure_reference: str, evidence_ids: Iterable[str]) -> DiscrepancyRecord:
        """Close a discrepancy only with a reference and evidence."""
        evidence = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        if not closure_reference.strip() or not evidence:
            raise ValueError("discrepancy closure requires closure_reference and evidence_ids")
        current = self._records[discrepancy_id]
        updated = current.model_copy(update={"status": "closed", "closed_at": datetime.now(timezone.utc), "evidence_ids": tuple(dict.fromkeys(current.evidence_ids + evidence))})
        self._records[discrepancy_id] = updated
        self.record_decision(f"close:{discrepancy_id}", "closed", closure_reference)
        return updated

    def get(self, discrepancy_id: str) -> DiscrepancyRecord:
        """Return one discrepancy."""
        return self._records[discrepancy_id]

    def all(self) -> tuple[DiscrepancyRecord, ...]:
        """Return all records in stable insertion order."""
        return tuple(self._records.values())

    def by_scenario(self, scenario_id: str) -> tuple[DiscrepancyRecord, ...]:
        """Return discrepancies for a scenario."""
        return tuple(item for item in self._records.values() if item.scenario_id == scenario_id)

    def by_type(self, discrepancy_type: DiscrepancyType | str) -> tuple[DiscrepancyRecord, ...]:
        """Return discrepancies for a category."""
        selected = DiscrepancyType(discrepancy_type)
        return tuple(item for item in self._records.values() if item.discrepancy_type == selected)
