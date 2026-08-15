"""Scheduled maintenance governance without automatic production execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable

from change_management.change_models import MaintenanceWindow


class MaintenanceState(str, Enum):
    """Maintenance lifecycle states."""

    SCHEDULED = "scheduled"
    BLOCKED = "blocked"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class MaintenanceRequest:
    """A maintenance request with explicit scope and approval references."""

    maintenance_id: str
    title: str
    window: MaintenanceWindow
    target_ids: tuple[str, ...]
    approved: bool = False
    approval_reference: str = ""
    production_requested: bool = False
    actor: str = ""
    change_id: str = ""
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize a maintenance request."""
        return asdict(self) | {"window": self.window.to_dict(), "target_ids": list(self.target_ids), "evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class MaintenanceDecision:
    """Governance decision for a maintenance lifecycle action."""

    maintenance_id: str
    allowed: bool
    state: str
    gate: str
    reasons: tuple[str, ...] = ()
    required_human_inputs: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the decision."""
        return asdict(self) | {"reasons": list(self.reasons), "required_human_inputs": list(self.required_human_inputs), "evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class MaintenanceRecord:
    """Stored scheduled maintenance record."""

    request: MaintenanceRequest
    state: str
    scheduled_at: str
    decision: MaintenanceDecision

    def to_dict(self) -> dict[str, Any]:
        """Serialize the record."""
        return {"request": self.request.to_dict(), "state": self.state, "scheduled_at": self.scheduled_at, "decision": self.decision.to_dict()}


class MaintenanceManager:
    """Schedule and govern maintenance windows; never execute network changes."""

    def __init__(self, *, audit_trail: Any | None = None) -> None:
        """Create an in-memory maintenance calendar."""
        self.audit_trail = audit_trail
        self._records: dict[str, MaintenanceRecord] = {}

    def schedule(self, request: MaintenanceRequest) -> MaintenanceRecord:
        """Validate and register one maintenance request."""
        decision = self._evaluate(request)
        state = MaintenanceState.SCHEDULED.value if decision.allowed else MaintenanceState.BLOCKED.value
        record = MaintenanceRecord(request, state, datetime.now(timezone.utc).isoformat(), decision)
        if decision.allowed:
            self._records[request.maintenance_id] = record
        self._audit(record)
        return record

    def start(self, maintenance_id: str, *, now: datetime | None = None) -> MaintenanceDecision:
        """Mark a scheduled window active only when current time is inside it."""
        record = self.get(maintenance_id)
        current = now or datetime.now(timezone.utc)
        window = record.request.window
        if record.state != MaintenanceState.SCHEDULED.value:
            decision = MaintenanceDecision(maintenance_id, False, record.state, "blocked", (f"maintenance is not scheduled: {record.state}",), (), record.request.evidence_ids)
        elif current.tzinfo is None or not window.start_time <= current <= window.end_time:
            decision = MaintenanceDecision(maintenance_id, False, MaintenanceState.SCHEDULED.value, "blocked", ("current time is outside the approved maintenance window",), ("enter_maintenance_window",), record.request.evidence_ids)
        else:
            decision = MaintenanceDecision(maintenance_id, True, MaintenanceState.ACTIVE.value, "allow_with_change_control", (), (), record.request.evidence_ids)
            self._records[maintenance_id] = MaintenanceRecord(record.request, MaintenanceState.ACTIVE.value, record.scheduled_at, decision)
        self._audit(self._records.get(maintenance_id, record))
        return decision

    def complete(self, maintenance_id: str) -> MaintenanceDecision:
        """Close an active maintenance record without asserting technical success."""
        record = self.get(maintenance_id)
        if record.state != MaintenanceState.ACTIVE.value:
            decision = MaintenanceDecision(maintenance_id, False, record.state, "blocked", ("only an active maintenance window can be completed",), (), record.request.evidence_ids)
        else:
            decision = MaintenanceDecision(maintenance_id, True, MaintenanceState.COMPLETED.value, "review_required", ("technical completion must be verified separately",), (), record.request.evidence_ids)
            self._records[maintenance_id] = MaintenanceRecord(record.request, MaintenanceState.COMPLETED.value, record.scheduled_at, decision)
        self._audit(self._records.get(maintenance_id, record))
        return decision

    def cancel(self, maintenance_id: str) -> MaintenanceDecision:
        """Cancel a scheduled or active maintenance record."""
        record = self.get(maintenance_id)
        if record.state in {MaintenanceState.COMPLETED.value, MaintenanceState.CANCELLED.value}:
            decision = MaintenanceDecision(maintenance_id, False, record.state, "blocked", (f"maintenance cannot be cancelled from state {record.state}",), (), record.request.evidence_ids)
        else:
            decision = MaintenanceDecision(maintenance_id, True, MaintenanceState.CANCELLED.value, "allow", (), (), record.request.evidence_ids)
            self._records[maintenance_id] = MaintenanceRecord(record.request, MaintenanceState.CANCELLED.value, record.scheduled_at, decision)
        self._audit(self._records.get(maintenance_id, record))
        return decision

    def get(self, maintenance_id: str) -> MaintenanceRecord:
        """Return one scheduled maintenance record."""
        try:
            return self._records[maintenance_id]
        except KeyError as exc:
            raise KeyError(f"maintenance record not found: {maintenance_id}") from exc

    def scheduled(self) -> tuple[MaintenanceRecord, ...]:
        """Return active calendar records in deterministic order."""
        return tuple(self._records[key] for key in sorted(self._records))

    def _evaluate(self, request: MaintenanceRequest) -> MaintenanceDecision:
        """Evaluate window validity, approval, notification, and target conflicts."""
        reasons: list[str] = []
        required: list[str] = []
        window = request.window
        if not request.maintenance_id or not request.title:
            reasons.append("maintenance_id and title are required")
        if not request.target_ids:
            reasons.append("at least one target ID is required")
            required.append("target_ids")
        if window.end_time <= window.start_time:
            reasons.append("maintenance window end must be later than start")
        if window.start_time.tzinfo is None or window.end_time.tzinfo is None:
            reasons.append("maintenance timestamps must include timezone information")
        if not window.business_justification.strip():
            reasons.append("maintenance window business justification is required")
            required.append("business_justification")
        if not window.affected_users_notified:
            reasons.append("affected users must be notified before scheduling")
            required.append("affected_users_notified")
        if request.production_requested and not request.approved:
            reasons.append("production maintenance requires explicit approval")
            required.append("approved")
        if request.production_requested and not request.approval_reference:
            reasons.append("production maintenance approval reference is missing")
            required.append("approval_reference")
        if request.approval_reference and not request.approval_reference.startswith("approval://"):
            reasons.append("approval reference must use the approval:// scheme")
            required.append("approval_reference")
        if request.production_requested and not request.actor:
            reasons.append("production maintenance requires an identified actor")
            required.append("actor")
        for existing in self._records.values():
            if existing.state in {MaintenanceState.CANCELLED.value, MaintenanceState.COMPLETED.value}:
                continue
            if set(existing.request.target_ids).intersection(request.target_ids) and self._overlaps(existing.request.window, request.window):
                reasons.append(f"maintenance conflicts with scheduled record {existing.request.maintenance_id}")
        allowed = not reasons
        return MaintenanceDecision(request.maintenance_id, allowed, MaintenanceState.SCHEDULED.value if allowed else MaintenanceState.BLOCKED.value, "allow_with_change_control" if allowed else "blocked", tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(required)), request.evidence_ids)

    @staticmethod
    def _overlaps(first: MaintenanceWindow, second: MaintenanceWindow) -> bool:
        """Return whether two windows overlap."""
        return first.start_time < second.end_time and second.start_time < first.end_time

    def _audit(self, record: MaintenanceRecord) -> None:
        """Record maintenance metadata without network commands."""
        if self.audit_trail is None:
            return
        self.audit_trail.record("operations.maintenance", "maintenance_manager", {"maintenance_id": record.request.maintenance_id, "change_id": record.request.change_id, "target_ids": list(record.request.target_ids), "state": record.state, "gate": record.decision.gate, "evidence_ids": list(record.request.evidence_ids)}, outcome=record.state)
