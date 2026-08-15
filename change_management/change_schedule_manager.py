"""Maintenance-window scheduling and local change calendar."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .change_conflict_detector import ChangeConflictDetector
from .change_freeze_manager import ChangeFreezeManager
from .change_models import ChangeRequest, ChangeStatus, ChangeType, MaintenanceWindow


class ChangeScheduleManager:
    """Schedule changes only inside approved windows and freeze policy."""

    def __init__(self, freeze_manager: ChangeFreezeManager | None = None, conflict_detector: ChangeConflictDetector | None = None) -> None:
        """Create a local scheduler."""
        self.freeze_manager = freeze_manager or ChangeFreezeManager()
        self.conflict_detector = conflict_detector or ChangeConflictDetector()
        self._windows: list[MaintenanceWindow] = []
        self._scheduled: dict[str, ChangeRequest] = {}

    def add_window(self, window: MaintenanceWindow) -> MaintenanceWindow:
        """Add an approved maintenance window."""
        if window.end_time <= window.start_time:
            raise ValueError("maintenance window end must be later than start")
        self._windows.append(window)
        return window

    def windows(self) -> tuple[MaintenanceWindow, ...]:
        """Return maintenance windows in order."""
        return tuple(sorted(self._windows, key=lambda item: item.start_time))

    def schedule(self, request: ChangeRequest, window: MaintenanceWindow, *, emergency_override: bool = False, enhanced_approval: bool = False, dependencies: Mapping[str, Iterable[str]] | None = None) -> ChangeRequest:
        """Schedule a request after window, freeze, and conflict checks."""
        if request.change_type != ChangeType.EMERGENCY.value and not self._inside_window(window):
            raise ValueError("normal and standard changes must use an approved maintenance window")
        freeze = self.freeze_manager.evaluate(request, window.start_time, window.end_time, emergency_override=emergency_override, enhanced_approval=enhanced_approval)
        if not freeze.allowed:
            raise ValueError("change is blocked by an active freeze: " + "; ".join(freeze.reasons))
        request.scheduled_window = window
        report = self.conflict_detector.detect(tuple(self._scheduled.values()) + (request,), dependencies=dependencies)
        if report.blocking:
            request.scheduled_window = None
            raise ValueError("change schedule conflicts detected")
        request.status = ChangeStatus.SCHEDULED.value
        request.updated_at = datetime.now(timezone.utc)
        self._scheduled[request.change_id] = request
        return request

    def unschedule(self, change_id: str) -> ChangeRequest:
        """Remove a scheduled change before execution."""
        request = self._scheduled.pop(change_id)
        request.scheduled_window = None
        request.status = ChangeStatus.PLAN_COMPLETE.value
        request.updated_at = datetime.now(timezone.utc)
        return request

    def scheduled(self) -> tuple[ChangeRequest, ...]:
        """Return scheduled requests."""
        return tuple(sorted(self._scheduled.values(), key=lambda item: (item.scheduled_window.start_time if item.scheduled_window else datetime.max.replace(tzinfo=timezone.utc), item.change_id)))

    def export_ical(self) -> str:
        """Export scheduled changes as a minimal iCalendar text representation."""
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AutoNetArchitect//ChangeManagement//EN"]
        for request in self.scheduled():
            window = request.scheduled_window
            if window is None:
                continue
            lines.extend(("BEGIN:VEVENT", f"UID:{request.change_id}@autonetarchitect", f"DTSTART:{window.start_time.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}", f"DTEND:{window.end_time.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}", f"SUMMARY:{request.title}", f"DESCRIPTION:{request.description}", "END:VEVENT"))
        lines.append("END:VCALENDAR")
        return "\n".join(lines) + "\n"

    def _inside_window(self, window: MaintenanceWindow) -> bool:
        """Require the supplied interval to be in the local approved calendar."""
        return any(item.start_time <= window.start_time and item.end_time >= window.end_time for item in self._windows)
