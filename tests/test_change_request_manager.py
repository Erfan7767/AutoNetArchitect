from change_management import ChangeRequestManager, ChangeStatus, ClosureCode


def test_change_request_manager_creates_updates_submits_and_closes():
    manager = ChangeRequestManager()
    request = manager.create("Test change", "Detailed description", "alice")
    assert request.change_id.startswith("CHG-")
    manager.update(request.change_id, priority="high")
    manager.submit(request.change_id)
    assert manager.get(request.change_id).status == ChangeStatus.SUBMITTED.value
    manager.get(request.change_id).status = ChangeStatus.COMPLETED.value
    closed = manager.close(request.change_id, ClosureCode.SUCCESSFUL.value, lessons_learned="validated")
    assert closed.closure_code == ClosureCode.SUCCESSFUL.value
    assert len(closed.history_ids) >= 3


def test_change_request_manager_blocks_edit_after_approval():
    manager = ChangeRequestManager()
    request = manager.create("Test", "Description", "alice")
    request.status = ChangeStatus.APPROVED.value
    rejected = False
    try:
        manager.update(request.change_id, title="new")
    except ValueError:
        rejected = True
    assert rejected is True
