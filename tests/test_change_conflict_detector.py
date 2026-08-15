from datetime import datetime, timedelta, timezone

from change_management import ChangeConflictDetector, ChangeRequest, ConfigChange, DeviceRef, MaintenanceWindow, ServiceRef


def test_change_conflict_detector_detects_device_service_and_logical_conflicts():
    window = MaintenanceWindow(datetime(2026, 3, 1, tzinfo=timezone.utc), datetime(2026, 3, 1, 2, tzinfo=timezone.utc), "UTC", "window")
    left = ChangeRequest("CHG-17", "Left", "Detailed", "alice", affected_devices=[DeviceRef("edge-1")], affected_services=[ServiceRef("dns")], config_changes=[ConfigChange("edge-1", "edge-1", "routing", after_config="cost 10")], scheduled_window=window)
    right = ChangeRequest("CHG-18", "Right", "Detailed", "bob", affected_devices=[DeviceRef("edge-1")], affected_services=[ServiceRef("dns")], config_changes=[ConfigChange("edge-1", "edge-1", "routing", after_config="cost 100")], scheduled_window=window)
    report = ChangeConflictDetector().detect([left, right])
    types = {conflict.conflict_type for conflict in report.conflicts}
    assert report.blocking is True
    assert {"device_conflict", "service_conflict", "logical_conflict"}.issubset(types)
