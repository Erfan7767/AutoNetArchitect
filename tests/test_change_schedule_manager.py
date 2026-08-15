from datetime import datetime, timedelta, timezone

from change_management import ChangeRequest, ChangeScheduleManager, MaintenanceWindow


def _window(start):
    return MaintenanceWindow(start, start + timedelta(hours=2), "UTC", "planned change", True)


def test_change_schedule_manager_schedules_inside_window_and_exports_ical():
    start = datetime(2026, 2, 1, 1, tzinfo=timezone.utc)
    manager = ChangeScheduleManager()
    approved_window = _window(start)
    manager.add_window(approved_window)
    request = ChangeRequest("CHG-9", "Scheduled", "Detailed", "alice", status="approved")
    manager.schedule(request, approved_window)
    assert request.status == "scheduled"
    assert "BEGIN:VCALENDAR" in manager.export_ical()
    assert "CHG-9" in manager.export_ical()


def test_change_schedule_manager_blocks_overlapping_device_changes():
    start = datetime(2026, 2, 1, 1, tzinfo=timezone.utc)
    manager = ChangeScheduleManager()
    window = _window(start)
    manager.add_window(window)
    first = ChangeRequest("CHG-10", "One", "Detailed", "alice", status="approved")
    second = ChangeRequest("CHG-11", "Two", "Detailed", "bob", status="approved")
    from change_management import DeviceRef
    first.affected_devices.append(DeviceRef("edge-1"))
    second.affected_devices.append(DeviceRef("edge-1"))
    manager.schedule(first, window)
    blocked = False
    try:
        manager.schedule(second, window)
    except ValueError:
        blocked = True
    assert blocked is True
