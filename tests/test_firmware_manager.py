from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import tempfile

from audit.audit_trail import AuditTrail
from change_management.change_models import MaintenanceWindow
from firmware import BootMode, FirmwareImage, FirmwareManager, FirmwareOperationState, FirmwareTarget, FirmwareUpgradeRequest, UpgradePath


PAYLOAD = b"firmware image bytes for tests"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


def _image(**overrides):
    values = {"image_id": "IMG-1", "vendor": "cisco", "platform": "ios_xe", "model": "C9300-48P", "version": "17.9.4", "expected_sha256": DIGEST, "artifact_reference": "artifact://IMG-1", "boot_mode": BootMode.INSTALL.value, "evidence_ids": ("ev-image-1",)}
    values.update(overrides)
    return FirmwareImage(**values)


def _target(**overrides):
    values = {"target_id": "T-1", "device_id": "edge-1", "vendor": "cisco", "platform": "ios_xe", "model": "C9300-48P", "current_version": "17.6.5", "current_boot_mode": BootMode.INSTALL.value, "redundancy_group": "edge-pair-1", "redundancy_role": "primary", "management_reference": "oob://edge-1"}
    values.update(overrides)
    return FirmwareTarget(**values)


def _path(**overrides):
    values = {"path_id": "PATH-1", "vendor": "cisco", "platform": "ios_xe", "model": "C9300-48P", "current_version": "17.6.5", "target_version": "17.9.4", "source_boot_mode": BootMode.INSTALL.value, "target_boot_mode": BootMode.INSTALL.value, "support_state": "supported", "rollback_image_id": "IMG-ROLLBACK", "evidence_ids": ("ev-path-1",)}
    values.update(overrides)
    return UpgradePath(**values)


def _window():
    start = datetime.now(timezone.utc) + timedelta(hours=1)
    return MaintenanceWindow(start, start + timedelta(hours=2), "UTC", "approved firmware maintenance", True, start - timedelta(minutes=10))


def _request(**overrides):
    values = {"request_id": "REQ-1", "target": _target(), "image": _image(), "maintenance_window": _window(), "approved": True, "approval_reference": "approval://CHG-1", "project_valid": True, "production_requested": True, "dry_run": False, "rollback_required": True, "rollback_image_id": "IMG-ROLLBACK", "upgrade_path_id": "PATH-1", "actor": "operator-1", "evidence_ids": ("ev-request-1",)}
    values.update(overrides)
    return FirmwareUpgradeRequest(**values)


def _manager(audit=None):
    manager = FirmwareManager(audit_trail=audit)
    manager.register_image(_image())
    manager.register_upgrade_path(_path())
    return manager


def test_firmware_manager_verifies_sha256_and_detects_mismatch():
    manager = FirmwareManager()
    image = _image()
    verified = manager.verify_image(image, PAYLOAD)
    assert verified.verified is True
    assert verified.status == "verified"
    mismatch = manager.verify_image(image, b"different bytes")
    assert mismatch.verified is False
    assert mismatch.status == "hash_mismatch"


def test_firmware_manager_resolves_only_exact_registered_path():
    manager = _manager()
    assert manager.resolve_path(_request()) is not None
    assert manager.resolve_path(_request(target=_target(model="C9300-24P"))) is None
    assert manager.resolve_path(_request(target=_target(current_boot_mode=BootMode.BUNDLE.value))) is None


def test_firmware_manager_dry_run_does_not_invoke_driver():
    manager = _manager()
    calls = []
    result = manager.execute(_request(dry_run=True, production_requested=False), driver=lambda payload: calls.append(payload))
    assert result.state == FirmwareOperationState.DRY_RUN.value
    assert result.gate == "review_only"
    assert result.operation is not None and result.operation.executed is False
    assert calls == []


def test_firmware_manager_real_execution_requires_window_approval_and_integrity():
    manager = _manager()
    missing_window = manager.execute(_request(maintenance_window=None))
    assert missing_window.state == FirmwareOperationState.BLOCKED.value
    assert "maintenance_window" in missing_window.required_human_inputs
    missing_approval = manager.execute(_request(approved=False))
    assert missing_approval.state == FirmwareOperationState.BLOCKED.value
    assert "approved" in missing_approval.required_human_inputs
    bad_hash = manager.execute(_request(image=_image(expected_sha256="0" * 64)), artifact_bytes=PAYLOAD)
    assert bad_hash.state == FirmwareOperationState.BLOCKED.value
    assert "verified_firmware_image_sha256" in bad_hash.required_human_inputs


def test_firmware_manager_executes_approved_exact_path_and_redacts_output():
    audit_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    audit_file.close()
    audit = AuditTrail(audit_file.name)
    manager = _manager(audit)
    result = manager.execute(_request(), artifact_bytes=PAYLOAD, driver=lambda payload: {"status": "success", "output": "password=raw-secret", "provider_reference": "fw-session-1", "evidence_ids": ["ev-exec-1"]})
    assert result.state == FirmwareOperationState.EXECUTED.value
    assert result.gate == "allow"
    assert result.operation is not None
    assert "raw-secret" not in result.operation.output
    assert "ev-exec-1" in result.evidence_ids
    assert len(audit.query(event_type="firmware.upgrade")) == 1


def test_firmware_manager_blocks_unknown_path_without_guessing():
    manager = FirmwareManager()
    manager.register_image(_image())
    result = manager.execute(_request(upgrade_path_id="PATH-DOES-NOT-EXIST"), artifact_bytes=PAYLOAD, driver=lambda payload: {"status": "success"})
    assert result.state == FirmwareOperationState.BLOCKED.value
    assert "exact_upgrade_path_evidence" in result.required_human_inputs
