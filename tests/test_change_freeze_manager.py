from datetime import datetime, timezone

from change_management import ChangeFreezeManager, ChangeRequest, FreezeType, FreezeWindow


def test_change_freeze_manager_blocks_normal_change_during_full_freeze():
    manager = ChangeFreezeManager()
    manager.add_window(FreezeWindow("freeze-1", datetime(2026, 4, 1, tzinfo=timezone.utc), datetime(2026, 4, 2, tzinfo=timezone.utc), FreezeType.FULL_FREEZE.value, "quarter close"))
    request = ChangeRequest("CHG-19", "Normal", "Detailed", "alice", change_type="normal")
    result = manager.evaluate(request, datetime(2026, 4, 1, 1, tzinfo=timezone.utc), datetime(2026, 4, 1, 2, tzinfo=timezone.utc))
    assert result.allowed is False
    assert result.override_record_required is True


def test_change_freeze_manager_allows_emergency_override_with_enhanced_approval():
    manager = ChangeFreezeManager()
    manager.add_window(FreezeWindow("freeze-2", datetime(2026, 4, 1, tzinfo=timezone.utc), datetime(2026, 4, 2, tzinfo=timezone.utc), FreezeType.FULL_FREEZE.value, "quarter close"))
    request = ChangeRequest("CHG-20", "Emergency", "Detailed", "alice", change_type="emergency")
    result = manager.evaluate(request, datetime(2026, 4, 1, 1, tzinfo=timezone.utc), datetime(2026, 4, 1, 2, tzinfo=timezone.utc), emergency_override=True, enhanced_approval=True)
    assert result.allowed is True
