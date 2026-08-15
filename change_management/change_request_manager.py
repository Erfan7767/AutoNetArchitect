"""Local-first CRUD and lifecycle entry points for change requests."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable, Iterable, Mapping

from designers.base_designer import Assumption, DecisionRecord

from .change_models import (
    ChangeCategory,
    ChangePriority,
    ChangeRequest,
    ChangeStatus,
    ChangeType,
    ClosureCode,
    ConfigChange,
    DeviceRef,
    ServiceRef,
    SiteRef,
)


class ChangeRequestManager:
    """Manage change requests in an in-memory V1 repository."""

    EDITABLE_STATUSES = {ChangeStatus.DRAFT.value, ChangeStatus.SUBMITTED.value, ChangeStatus.RISK_ASSESSED.value, ChangeStatus.IMPACT_ASSESSED.value}

    def __init__(self, history_recorder: Callable[[str, str, Mapping[str, Any]], str] | None = None) -> None:
        """Create a thread-safe local manager."""
        self._requests: dict[str, ChangeRequest] = {}
        self._sequence = 0
        self._lock = RLock()
        self._history_recorder = history_recorder

    def create(
        self,
        title: str,
        description: str,
        requester: str,
        *,
        change_type: str = ChangeType.NORMAL.value,
        change_category: str = ChangeCategory.CONFIGURATION.value,
        priority: str = ChangePriority.MEDIUM.value,
        affected_devices: Iterable[DeviceRef] = (),
        affected_services: Iterable[ServiceRef] = (),
        affected_sites: Iterable[SiteRef] = (),
        related_project: str = "",
        config_changes: Iterable[ConfigChange] = (),
    ) -> ChangeRequest:
        """Create a validated draft change request."""
        if not title or not description or not requester:
            raise ValueError("title, description, and requester are required")
        if change_type not in {item.value for item in ChangeType}:
            raise ValueError("unsupported change type")
        if change_category not in {item.value for item in ChangeCategory}:
            raise ValueError("unsupported change category")
        if priority not in {item.value for item in ChangePriority}:
            raise ValueError("unsupported change priority")
        with self._lock:
            now = datetime.now(timezone.utc)
            change_id = self._next_id(now)
            request = ChangeRequest(change_id, title, description, requester, change_type, change_category, priority, ChangeStatus.DRAFT.value, list(affected_devices), list(affected_services), list(affected_sites), related_project, list(config_changes), created_at=now, updated_at=now)
            request.decision_records.append(DecisionRecord("ChangeRequestManager", f"{change_id}:creation", "create_local_change_request", ["external_itsm_request"], {"external_itsm_request": "V1 local-first scope does not assume an ITSM integration"}))
            request.assumptions.append(Assumption("change_request_evidence", "human_supplied_request", "V1 does not infer business intent or scope from an external ITSM", True))
            self._requests[change_id] = request
            self._record_history(change_id, "created", {"requester": requester, "change_type": change_type})
            return request

    def get(self, change_id: str) -> ChangeRequest:
        """Return a change request by ID."""
        with self._lock:
            try:
                return self._requests[change_id]
            except KeyError as exc:
                raise KeyError(f"change request not found: {change_id}") from exc

    def list(self, *, status: str | None = None, requester: str | None = None, change_type: str | None = None) -> tuple[ChangeRequest, ...]:
        """List change requests using deterministic filters."""
        with self._lock:
            values = [item for item in self._requests.values() if (status is None or item.status == status) and (requester is None or item.requester == requester) and (change_type is None or item.change_type == change_type)]
            return tuple(sorted(values, key=lambda item: item.change_id))

    def update(self, change_id: str, **changes: Any) -> ChangeRequest:
        """Update editable fields before approval."""
        with self._lock:
            request = self.get(change_id)
            if request.status not in self.EDITABLE_STATUSES:
                raise ValueError("change request is no longer editable")
            allowed = {"title", "description", "change_type", "change_category", "priority", "affected_devices", "affected_services", "affected_sites", "related_project", "config_changes"}
            unknown = set(changes) - allowed
            if unknown:
                raise ValueError(f"unsupported update fields: {sorted(unknown)}")
            for key, value in changes.items():
                if key in {"change_type", "change_category", "priority"} and not isinstance(value, str):
                    raise TypeError(f"{key} must be a string enum value")
                setattr(request, key, value)
            request.updated_at = datetime.now(timezone.utc)
            request.decision_records.append(DecisionRecord("ChangeRequestManager", f"{change_id}:update:{request.updated_at.isoformat()}", "update_request_before_approval", list(changes), {}))
            self._record_history(change_id, "updated", {"fields": sorted(changes)})
            return request

    def submit(self, change_id: str) -> ChangeRequest:
        """Submit a draft for assessment."""
        with self._lock:
            request = self.get(change_id)
            if request.status != ChangeStatus.DRAFT.value:
                raise ValueError("only draft changes can be submitted")
            request.status = ChangeStatus.SUBMITTED.value
            request.updated_at = datetime.now(timezone.utc)
            request.decision_records.append(DecisionRecord("ChangeRequestManager", f"{change_id}:submit", "submitted_for_assessment", ["remain_draft"], {"remain_draft": "requester explicitly submitted the change"}))
            self._record_history(change_id, "submitted", {})
            return request

    def close(self, change_id: str, closure_code: str, *, lessons_learned: str = "") -> ChangeRequest:
        """Close a terminal request with an explicit closure code."""
        if closure_code not in {item.value for item in ClosureCode}:
            raise ValueError("unsupported closure code")
        with self._lock:
            request = self.get(change_id)
            if request.status not in {ChangeStatus.COMPLETED.value, ChangeStatus.FAILED.value, ChangeStatus.ROLLED_BACK.value, ChangeStatus.CANCELLED.value}:
                raise ValueError("only terminal changes can be closed")
            now = datetime.now(timezone.utc)
            request.closed_at = now
            request.updated_at = now
            request.closure_code = closure_code
            request.lessons_learned = lessons_learned
            self._record_history(change_id, "closed", {"closure_code": closure_code})
            return request

    def _next_id(self, now: datetime) -> str:
        """Generate a date-scoped sequential ID."""
        self._sequence += 1
        return f"CHG-{now.strftime('%Y%m%d')}-{self._sequence:04d}"

    def _record_history(self, change_id: str, event: str, details: Mapping[str, Any]) -> None:
        """Record local history and optionally call a history adapter."""
        request = self._requests[change_id]
        history_id = f"{change_id}:{len(request.history_ids) + 1:04d}"
        request.history_ids.append(history_id)
        if self._history_recorder is not None:
            self._history_recorder(change_id, event, details)
