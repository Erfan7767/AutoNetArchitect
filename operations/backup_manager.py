"""Safe local backup management for operational artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Iterable

from log_redaction.redacting_filter import RedactingFilter


class BackupStatus:
    """Stable backup state values."""

    CREATED = "created"
    CREATED_REDACTED = "created_redacted"
    VERIFIED = "verified"
    FAILED = "failed"
    NOT_VERIFIABLE = "not_verifiable_with_current_inputs"


@dataclass(frozen=True)
class BackupArtifact:
    """Reference and integrity metadata for one local backup artifact."""

    backup_id: str
    target_id: str
    created_at: str
    storage_path: str
    backup_reference: str
    sha256: str
    status: str
    redacted: bool = False
    evidence_ids: tuple[str, ...] = ()
    source_reference: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize backup metadata without content bytes."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class BackupVerification:
    """Verification result for a backup artifact."""

    backup_id: str
    verified: bool
    status: str
    expected_sha256: str
    actual_sha256: str = ""
    reason: str = ""
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize verification metadata."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


class BackupManager:
    """Create and verify local backups atomically without remote restore execution."""

    def __init__(self, *, audit_trail: Any | None = None) -> None:
        """Create an empty local backup registry."""
        self.audit_trail = audit_trail
        self._artifacts: dict[str, BackupArtifact] = {}

    def create(self, backup_id: str, target_id: str, payload: bytes | str, storage_path: str | Path, *, backup_reference: str = "", evidence_ids: Iterable[str] = (), source_reference: str = "") -> BackupArtifact:
        """Write a sanitized backup atomically and register its digest."""
        if not backup_id or not target_id:
            raise ValueError("backup_id and target_id are required")
        if backup_reference and not backup_reference.startswith("backup://"):
            raise ValueError("backup_reference must use the backup:// scheme")
        path = Path(storage_path)
        raw = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        if not isinstance(raw, str):
            raise TypeError("backup payload must be bytes or text")
        sanitized = RedactingFilter.sanitize_value(raw)
        text = sanitized if isinstance(sanitized, str) else str(sanitized)
        redacted = text != raw
        data = text.encode("utf-8")
        temporary = path.with_suffix(path.suffix + ".tmp")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_bytes(data)
        temporary.replace(path)
        digest = hashlib.sha256(data).hexdigest()
        status = BackupStatus.CREATED_REDACTED if redacted else BackupStatus.CREATED
        artifact = BackupArtifact(backup_id, target_id, datetime.now(timezone.utc).isoformat(), str(path), backup_reference or f"backup://{backup_id}", digest, status, redacted, tuple(dict.fromkeys(str(item) for item in evidence_ids)), source_reference, "backup content is stored locally; no remote restore is performed by V1")
        self._artifacts[backup_id] = artifact
        self._audit("operations.backup_create", artifact, "success")
        return artifact

    def verify(self, backup_id: str) -> BackupVerification:
        """Verify the stored artifact digest without restoring it."""
        artifact = self.get(backup_id)
        path = Path(artifact.storage_path)
        if not path.exists():
            result = BackupVerification(backup_id, False, BackupStatus.NOT_VERIFIABLE, artifact.sha256, reason="backup storage path does not exist", evidence_ids=artifact.evidence_ids)
            self._audit("operations.backup_verify", artifact, result.status)
            return result
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            result = BackupVerification(backup_id, False, BackupStatus.NOT_VERIFIABLE, artifact.sha256, reason="backup storage path could not be read", evidence_ids=artifact.evidence_ids)
            self._audit("operations.backup_verify", artifact, result.status)
            return result
        verified = actual == artifact.sha256
        result = BackupVerification(backup_id, verified, BackupStatus.VERIFIED if verified else BackupStatus.FAILED, artifact.sha256, actual, "backup digest matches" if verified else "backup digest mismatch", artifact.evidence_ids)
        self._audit("operations.backup_verify", artifact, result.status)
        return result

    def get(self, backup_id: str) -> BackupArtifact:
        """Return one registered backup artifact."""
        try:
            return self._artifacts[backup_id]
        except KeyError as exc:
            raise KeyError(f"backup artifact not found: {backup_id}") from exc

    def list(self) -> tuple[BackupArtifact, ...]:
        """Return registered backups in deterministic order."""
        return tuple(self._artifacts[key] for key in sorted(self._artifacts))

    def restore_preview(self, backup_id: str) -> dict[str, Any]:
        """Return review metadata only; V1 does not perform restore execution."""
        artifact = self.get(backup_id)
        verification = self.verify(backup_id)
        return {"backup_id": backup_id, "preview_only": True, "remote_restore_executed": False, "verification": verification.to_dict(), "storage_path": artifact.storage_path, "backup_reference": artifact.backup_reference}

    def _audit(self, event_type: str, artifact: BackupArtifact, outcome: str) -> None:
        """Record backup metadata without content bytes."""
        if self.audit_trail is None:
            return
        self.audit_trail.record(event_type, "backup_manager", {"backup_id": artifact.backup_id, "target_id": artifact.target_id, "backup_reference": artifact.backup_reference, "sha256": artifact.sha256, "status": artifact.status, "redacted": artifact.redacted, "evidence_ids": list(artifact.evidence_ids)}, outcome=outcome)
