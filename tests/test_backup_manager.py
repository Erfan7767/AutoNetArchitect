import tempfile
from pathlib import Path

from operations import BackupManager, BackupStatus


def test_backup_manager_creates_and_verifies_atomic_local_backup():
    with tempfile.TemporaryDirectory() as directory:
        manager = BackupManager()
        path = Path(directory) / "edge-1.cfg"
        artifact = manager.create("BACKUP-1", "edge-1", "hostname edge-1\n", path, backup_reference="backup://BACKUP-1", evidence_ids=("ev-backup",))
        assert artifact.status == BackupStatus.CREATED
        assert path.exists()
        verification = manager.verify("BACKUP-1")
        assert verification.verified is True
        assert verification.status == BackupStatus.VERIFIED
        assert "ev-backup" in verification.evidence_ids


def test_backup_manager_detects_tampering_and_does_not_restore_remotely():
    with tempfile.TemporaryDirectory() as directory:
        manager = BackupManager()
        path = Path(directory) / "edge-2.cfg"
        manager.create("BACKUP-2", "edge-2", "hostname edge-2\n", path)
        path.write_text("tampered\n", encoding="utf-8")
        verification = manager.verify("BACKUP-2")
        assert verification.verified is False
        assert verification.status == BackupStatus.FAILED
        preview = manager.restore_preview("BACKUP-2")
        assert preview["preview_only"] is True
        assert preview["remote_restore_executed"] is False


def test_backup_manager_rejects_non_reference_backup_scheme():
    with tempfile.TemporaryDirectory() as directory:
        try:
            BackupManager().create("BACKUP-3", "edge-3", "config", Path(directory) / "edge-3.cfg", backup_reference="raw-reference")
        except ValueError as error:
            assert "backup://" in str(error)
        else:
            raise AssertionError("raw backup references must be rejected")
