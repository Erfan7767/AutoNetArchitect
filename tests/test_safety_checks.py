from datetime import datetime, timedelta, timezone
import hashlib

from change_management.change_models import MaintenanceWindow
from firmware import BootMode, FirmwareImage, FirmwareSafetyChecks, FirmwareTarget, FirmwareUpgradeRequest, ImageIntegrityResult, UpgradePath


def _request(**overrides):
    payload = b"firmware"
    digest = hashlib.sha256(payload).hexdigest()
    image = FirmwareImage("IMG-1", "juniper", "junos", "QFX5120", "21.4R3", digest, boot_mode=BootMode.PACKAGE.value, evidence_ids=("ev-img",))
    target = FirmwareTarget("T-1", "qfx-1", "juniper", "junos", "QFX5120", "20.4R3", BootMode.PACKAGE.value, "PAIR-1", "primary", management_reference="oob://qfx-1")
    path = UpgradePath("PATH-1", "juniper", "junos", "QFX5120", "20.4R3", "21.4R3", BootMode.PACKAGE.value, BootMode.PACKAGE.value, "supported", "ROLLBACK", ("ev-path",))
    start = datetime.now(timezone.utc) + timedelta(hours=1)
    window = MaintenanceWindow(start, start + timedelta(hours=1), "UTC", "firmware maintenance", True)
    values = {"request_id": "REQ-1", "target": target, "image": image, "maintenance_window": window, "approved": True, "approval_reference": "approval://CHG-1", "production_requested": True, "dry_run": False, "rollback_required": True, "rollback_image_id": "ROLLBACK", "actor": "operator"}
    values.update(overrides)
    return values, ImageIntegrityResult(True, "verified", digest, digest)


def test_safety_checks_require_exact_supported_path_and_traceable_evidence():
    values, integrity = _request()
    checks = FirmwareSafetyChecks()
    path = values["target"]
    assessment = checks.assess(values["request"] if "request" in values else FirmwareUpgradeRequest(**values), None, integrity)
    assert assessment.allowed is False
    assert "exact_upgrade_path_evidence" in assessment.required_human_inputs
    unsupported = UpgradePath("PATH-UNSUPPORTED", "juniper", "junos", "QFX5120", "20.4R3", "21.4R3", BootMode.PACKAGE.value, BootMode.PACKAGE.value, "unsupported", "ROLLBACK", ("ev-path",))
    assessment_unsupported = checks.assess(FirmwareUpgradeRequest(**values), unsupported, integrity)
    assert assessment_unsupported.allowed is False
    assert "registered upgrade path is not explicitly supported" in assessment_unsupported.reasons


def test_safety_checks_block_unknown_boot_mode_and_bootloader_execution():
    values, integrity = _request()
    request = FirmwareUpgradeRequest(**values)
    path = UpgradePath("PATH-BOOT", "juniper", "junos", "QFX5120", "20.4R3", "21.4R3", BootMode.UNKNOWN.value, BootMode.BOOTLOADER.value, "supported", "ROLLBACK", ("ev-path",))
    changed = FirmwareUpgradeRequest(**{**values, "target": FirmwareTarget("T-1", "qfx-1", "juniper", "junos", "QFX5120", "20.4R3", BootMode.UNKNOWN.value, "PAIR-1", "primary")})
    assessment = FirmwareSafetyChecks().assess(changed, path, integrity)
    assert assessment.allowed is False
    assert "confirmed_boot_mode" in assessment.required_human_inputs
    assert "supported_non_bootloader_upgrade_path" in assessment.required_human_inputs


def test_safety_checks_block_simultaneous_redundancy_group_member():
    values, integrity = _request()
    assessment = FirmwareSafetyChecks().assess(FirmwareUpgradeRequest(**values), UpgradePath("PATH-1", "juniper", "junos", "QFX5120", "20.4R3", "21.4R3", BootMode.PACKAGE.value, BootMode.PACKAGE.value, "supported", "ROLLBACK", ("ev-path",)), integrity, ("PAIR-1",))
    assert assessment.allowed is False
    assert "another member of the same redundancy group is already in flight" in assessment.reasons


def test_safety_checks_preview_can_be_created_without_production_window_but_not_real_execution():
    values, integrity = _request(dry_run=True, production_requested=False, maintenance_window=None, approved=False, approval_reference="", rollback_image_id="")
    request = FirmwareUpgradeRequest(**values)
    path = UpgradePath("PATH-1", "juniper", "junos", "QFX5120", "20.4R3", "21.4R3", BootMode.PACKAGE.value, BootMode.PACKAGE.value, "supported", "ROLLBACK", ("ev-path",))
    preview = FirmwareSafetyChecks().assess(request, path, integrity)
    assert preview.allowed is True
    real = FirmwareSafetyChecks().assess(FirmwareUpgradeRequest(**{**values, "dry_run": False, "production_requested": True}), path, integrity)
    assert real.allowed is False
    assert "maintenance_window" in real.required_human_inputs
    assert "approved" in real.required_human_inputs
