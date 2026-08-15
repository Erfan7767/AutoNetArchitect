from datetime import datetime, timedelta, timezone

from change_management.change_models import MaintenanceWindow
from operations import MaintenanceManager, MaintenanceRequest, MaintenanceState


def _request(maintenance_id="M-1", start_offset=1, **overrides):
    start = datetime.now(timezone.utc) + timedelta(hours=start_offset)
    window = MaintenanceWindow(start, start + timedelta(hours=1), "UTC", "planned network maintenance", True)
    values = {"maintenance_id": maintenance_id, "title": "edge maintenance", "window": window, "target_ids": ("edge-1",), "approved": True, "approval_reference": "approval://CHG-1", "production_requested": True, "actor": "operator", "change_id": "CHG-1", "evidence_ids": ("ev-maint",)}
    values.update(overrides)
    return MaintenanceRequest(**values)


def test_maintenance_manager_schedules_and_controls_window_lifecycle():
    manager = MaintenanceManager()
    request = _request()
    record = manager.schedule(request)
    assert record.state == MaintenanceState.SCHEDULED.value
    active = manager.start("M-1", now=request.window.start_time + timedelta(minutes=5))
    assert active.allowed is True
    assert active.state == MaintenanceState.ACTIVE.value
    completed = manager.complete("M-1")
    assert completed.allowed is True
    assert completed.state == MaintenanceState.COMPLETED.value
    assert "verified separately" in completed.reasons[0]


def test_maintenance_manager_blocks_missing_approval_or_notification():
    manager = MaintenanceManager()
    missing_approval = manager.schedule(_request(maintenance_id="M-2", approved=False, approval_reference=""))
    assert missing_approval.state == MaintenanceState.BLOCKED.value
    assert "approved" in missing_approval.decision.required_human_inputs
    missing_notification = manager.schedule(_request(maintenance_id="M-3", window=MaintenanceWindow(datetime.now(timezone.utc) + timedelta(hours=2), datetime.now(timezone.utc) + timedelta(hours=3), "UTC", "justification", False)))
    assert missing_notification.state == MaintenanceState.BLOCKED.value
    assert "affected_users_notified" in missing_notification.decision.required_human_inputs


def test_maintenance_manager_blocks_overlapping_target_windows_and_supports_cancel():
    manager = MaintenanceManager()
    first = manager.schedule(_request("M-4", start_offset=1))
    assert first.state == MaintenanceState.SCHEDULED.value
    second_window = MaintenanceWindow(first.request.window.start_time + timedelta(minutes=30), first.request.window.end_time + timedelta(minutes=30), "UTC", "overlap", True)
    second = manager.schedule(_request("M-5", window=second_window, change_id="CHG-2", approval_reference="approval://CHG-2"))
    assert second.state == MaintenanceState.BLOCKED.value
    assert "M-4" in second.decision.reasons[0]
    cancelled = manager.cancel("M-4")
    assert cancelled.allowed is True
    assert cancelled.state == MaintenanceState.CANCELLED.value
