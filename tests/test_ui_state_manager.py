"""Tests for local UI state and project locking."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from ui.state_manager import ProjectLock, ProjectLockError, UIStateManager, mask_for_ui


def test_ui_state_round_trip_and_secret_masking():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        manager = UIStateManager(root / "state.json")
        manager.set_project("project-1", "engineer")
        manager.update_values({"site": "hq", "password": "raw-password", "credential_reference": "secret://vault/device"})
        manager.set_workflow_context({"current_stage": "questionnaire", "token": "raw-token"})
        manager.add_approval_request(action="deployment", stage="deployment_execution", reasons=("approval required",))
        reloaded = UIStateManager(root / "state.json")
        snapshot = reloaded.snapshot().to_dict()
        assert snapshot["project_id"] == "project-1"
        assert snapshot["values"]["password"] == "<REDACTED>"
        assert snapshot["values"]["credential_reference"] == "secret://vault/device"
        assert snapshot["workflow_context"]["token"] == "<REDACTED>"
        assert snapshot["approval_requests"][0]["status"] == "pending"


def test_project_lock_is_exclusive_and_owner_safe():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = ProjectLock(root / "project.lock", actor="a", project_id="p")
        second = ProjectLock(root / "project.lock", actor="b", project_id="p")
        first.acquire()
        assert first.is_held() is True
        blocked = False
        try:
            second.acquire()
        except ProjectLockError:
            blocked = True
        if not blocked:
            raise AssertionError("second lock acquisition should fail")
        first.release()
        assert first.is_held() is False
        second.acquire()
        second.release()


def test_lock_context_releases_after_action():
    with TemporaryDirectory() as tmp:
        lock = ProjectLock(Path(tmp) / "project.lock", actor="engineer", project_id="p")
        with lock:
            assert lock.is_held() is True
        assert lock.is_held() is False


def test_mask_for_ui_is_recursive_and_secret_reference_safe():
    value = mask_for_ui({"token": "abc", "nested": [{"password": "def"}], "reference": "secret://vault/key"})
    assert value["token"] == "<REDACTED>"
    assert value["nested"][0]["password"] == "<REDACTED>"
    assert value["reference"] == "secret://vault/key"
