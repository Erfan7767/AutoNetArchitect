"""Tests for the human-authorized, secret-free site-agent backup handoff."""

from pathlib import Path

import pytest

from operations.backup_manager import BackupManager
from site_agent.backup_handoff import AgentBackupCaptureHandoff
from site_agent.models import DiscoveryResult, DiscoveryState, DiscoveryTarget, ManagementProtocol, ObservedDeviceFacts
from site_agent.scope import AuthorizedScope
from windows_app.workspace import WindowsWorkspace


def _scope() -> AuthorizedScope:
    return AuthorizedScope(
        site_id="site-01",
        approved_networks=("10.44.0.0/24",),
        approved_targets=("10.44.0.10",),
        allowed_protocols=(ManagementProtocol.SSH,),
        approval_reference="approval://site-01/discovery-and-backup",
        operator_acknowledged=True,
    )


def _discovery() -> DiscoveryResult:
    return DiscoveryResult(
        target=DiscoveryTarget(address="10.44.0.10", protocol=ManagementProtocol.SSH, credential_reference="credential://site-01/edge-01"),
        state=DiscoveryState.DISCOVERED,
        facts=ObservedDeviceFacts(vendor="cisco", platform="ios_xe", software_version="17.9.4", serial_reference="serial-ref-01", interface_count=48),
        message="Identity observed through the authorized read-only path.",
    )


def test_handoff_records_redacted_digest_verified_local_backup(tmp_path: Path) -> None:
    handoff = AgentBackupCaptureHandoff(BackupManager()).record_local_capture(
        capture_id="capture-01",
        scope=_scope(),
        discovery=_discovery(),
        backup_payload="hostname edge-01\npassword=must-not-leave-local-store",
        storage_path=tmp_path / "capture-01.txt",
        human_capture_authorization_reference="approval://change-44/backup-capture",
        evidence_ids=("evidence://discovery/edge-01",),
    )

    assert handoff.capture_state == "verified"
    assert handoff.automatic_capture_permitted is False
    assert handoff.backup_reference == "backup://capture-01"
    assert handoff.target_facts_hash != ""
    assert "password" not in handoff.model_dump_json().lower()


def test_handoff_blocks_unobserved_or_unauthorized_targets(tmp_path: Path) -> None:
    unauthorized = _discovery().model_copy(update={"target": DiscoveryTarget(address="10.44.0.11", protocol=ManagementProtocol.SSH, credential_reference="credential://site-01/other")})

    with pytest.raises(ValueError, match="authorized scope"):
        AgentBackupCaptureHandoff(BackupManager()).record_local_capture(
            capture_id="capture-02",
            scope=_scope(),
            discovery=unauthorized,
            backup_payload="non-sensitive material",
            storage_path=tmp_path / "capture-02.txt",
            human_capture_authorization_reference="approval://change-44/backup-capture",
        )


def test_handoff_requires_explicit_human_capture_authorization(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="approval://"):
        AgentBackupCaptureHandoff(BackupManager()).record_local_capture(
            capture_id="capture-03",
            scope=_scope(),
            discovery=_discovery(),
            backup_payload="non-sensitive material",
            storage_path=tmp_path / "capture-03.txt",
            human_capture_authorization_reference="human said yes",
        )


def test_workspace_persists_backup_handoff_metadata_without_content(tmp_path: Path) -> None:
    handoff = AgentBackupCaptureHandoff(BackupManager()).record_local_capture(
        capture_id="capture-04",
        scope=_scope(),
        discovery=_discovery(),
        backup_payload="hostname edge-01\npassword=not-for-handoff",
        storage_path=tmp_path / "capture-04.txt",
        human_capture_authorization_reference="approval://change-44/backup-capture",
    )

    workspace = WindowsWorkspace(tmp_path / "workspace")
    saved = workspace.save_backup_capture_handoff(handoff)
    loaded = workspace.load_backup_capture_handoff()
    raw = (tmp_path / "workspace" / "backup_capture_handoff.json").read_text(encoding="utf-8")

    assert loaded == saved
    assert "password" not in raw.lower()
