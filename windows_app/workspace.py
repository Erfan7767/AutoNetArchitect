"""Secret-free local workspace persistence for the Windows application."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from log_redaction.redacting_filter import RedactingFilter
from site_agent.backup_handoff import BackupCaptureHandoff
from site_agent.enrollment import EnrollmentReceipt
from site_agent.models import VirtualTestResult
from site_agent.scope import AuthorizedScope


class WindowsWorkspace:
    """Stores local discovery approval metadata without storing device credentials or collected secrets."""

    def __init__(self, root: Path) -> None:
        """Create a workspace rooted at a user-selected local directory."""

        self._root = root
        self._scope_path = root / "authorized_scope.json"
        self._virtual_validation_path = root / "virtual_validation_result.json"
        self._backup_handoff_path = root / "backup_capture_handoff.json"
        self._enrollment_receipt_path = root / "agent_enrollment_receipt.json"

    @property
    def root(self) -> Path:
        """Return the configured local workspace directory."""

        return self._root

    def save_scope(self, scope: AuthorizedScope) -> None:
        """Persist an approved discovery scope atomically with restrictive user-only permissions where supported."""

        self._root.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(scope.model_dump(mode="json"), indent=2, sort_keys=True)
        temporary = self._scope_path.with_suffix(".tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(self._scope_path)
        try:
            self._scope_path.chmod(0o600)
        except OSError:
            return

    def load_scope(self) -> AuthorizedScope | None:
        """Return the saved scope or ``None`` when discovery has not yet been approved."""

        if not self._scope_path.exists():
            return None
        raw: Any = json.loads(self._scope_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("The authorized discovery scope file is invalid.")
        return AuthorizedScope.model_validate(raw)

    def save_virtual_test_result(self, result: VirtualTestResult) -> VirtualTestResult:
        """Persist one redacted validation evidence record without configuration or credential material."""

        self._root.mkdir(parents=True, exist_ok=True)
        sanitized = result.model_copy(update={"detail": RedactingFilter.redact_text(result.detail)})
        temporary = self._virtual_validation_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(sanitized.model_dump(mode="json"), indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self._virtual_validation_path)
        try:
            self._virtual_validation_path.chmod(0o600)
        except OSError:
            return sanitized
        return sanitized

    def load_virtual_test_result(self) -> VirtualTestResult | None:
        """Return the latest local validation evidence without inferring a production action."""

        if not self._virtual_validation_path.exists():
            return None
        raw: Any = json.loads(self._virtual_validation_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("The local virtual validation result file is invalid.")
        return VirtualTestResult.model_validate(raw)

    def save_backup_capture_handoff(self, handoff: BackupCaptureHandoff) -> BackupCaptureHandoff:
        """Persist secret-free local backup-capture metadata without copying backup content."""

        self._root.mkdir(parents=True, exist_ok=True)
        sanitized = handoff.model_copy(update={"detail": RedactingFilter.redact_text(handoff.detail)})
        temporary = self._backup_handoff_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(sanitized.model_dump(mode="json"), indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self._backup_handoff_path)
        try:
            self._backup_handoff_path.chmod(0o600)
        except OSError:
            return sanitized
        return sanitized

    def load_backup_capture_handoff(self) -> BackupCaptureHandoff | None:
        """Return local backup-capture evidence only; never expose backup content or credentials."""

        if not self._backup_handoff_path.exists():
            return None
        raw: Any = json.loads(self._backup_handoff_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("The local backup handoff record is invalid.")
        return BackupCaptureHandoff.model_validate(raw)

    def save_enrollment_receipt(self, receipt: EnrollmentReceipt) -> EnrollmentReceipt:
        """Persist a secret-free mutual-enrollment receipt; private keys remain in the OS or hardware keystore."""

        self._root.mkdir(parents=True, exist_ok=True)
        temporary = self._enrollment_receipt_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(receipt.model_dump(mode="json"), indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self._enrollment_receipt_path)
        try:
            self._enrollment_receipt_path.chmod(0o600)
        except OSError:
            return receipt
        return receipt

    def load_enrollment_receipt(self) -> EnrollmentReceipt | None:
        """Return the saved enrollment receipt without retrieving, storing, or deriving a private key."""

        if not self._enrollment_receipt_path.exists():
            return None
        raw: Any = json.loads(self._enrollment_receipt_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("The local agent enrollment receipt file is invalid.")
        return EnrollmentReceipt.model_validate(raw)
