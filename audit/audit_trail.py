"""Tamper-evident, secret-safe audit trail for AutoNetArchitect."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable
import uuid

from log_redaction.redacting_filter import RedactingFilter


class AuditIntegrityError(RuntimeError):
    """Raised when an audit hash chain is invalid."""


@dataclass(frozen=True)
class AuditEntry:
    """One immutable audit record with no raw secret values."""

    entry_id: str
    timestamp: str
    event_type: str
    actor: str
    outcome: str
    details: dict[str, Any]
    previous_hash: str
    entry_hash: str
    source: str = "autonetarchitect"
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the audit entry."""
        return asdict(self)


class AuditTrail:
    """Append and query secret-safe audit entries using a hash chain."""

    REQUIRED_EVENT_TYPES = frozenset({"project.change", "config.generation", "deployment.attempt", "rollback.attempt", "secret.metadata_access"})

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._entries: list[AuditEntry] = []
        self._load()
        self.verify_integrity()

    def record(self, event_type: str, actor: str, details: dict[str, Any] | None = None, outcome: str = "success", source: str = "autonetarchitect", correlation_id: str | None = None) -> AuditEntry:
        """Append one sanitized audit entry."""
        if not event_type or not actor:
            raise ValueError("event_type and actor are required")
        sanitized = RedactingFilter.sanitize_value(details or {})
        if not isinstance(sanitized, dict):
            raise ValueError("audit details must be a mapping")
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        previous_hash = self._entries[-1].entry_hash if self._entries else "GENESIS"
        unsigned = {"entry_id": entry_id, "timestamp": timestamp, "event_type": event_type, "actor": actor, "outcome": outcome, "details": sanitized, "previous_hash": previous_hash, "source": source, "correlation_id": correlation_id}
        entry_hash = self._hash(unsigned)
        entry = AuditEntry(entry_id, timestamp, event_type, actor, outcome, sanitized, previous_hash, entry_hash, source, correlation_id)
        self._entries.append(entry)
        self._append(entry)
        return entry

    def record_project_change(self, actor: str, details: dict[str, Any], outcome: str = "success", correlation_id: str | None = None) -> AuditEntry:
        """Record a project change."""
        return self.record("project.change", actor, details, outcome, correlation_id=correlation_id)

    def record_config_generation(self, actor: str, details: dict[str, Any], outcome: str = "success", correlation_id: str | None = None) -> AuditEntry:
        """Record a configuration generation attempt."""
        return self.record("config.generation", actor, details, outcome, correlation_id=correlation_id)

    def record_deployment_attempt(self, actor: str, details: dict[str, Any], outcome: str = "attempted", correlation_id: str | None = None) -> AuditEntry:
        """Record a deployment attempt."""
        return self.record("deployment.attempt", actor, details, outcome, correlation_id=correlation_id)

    def record_rollback_attempt(self, actor: str, details: dict[str, Any], outcome: str = "attempted", correlation_id: str | None = None) -> AuditEntry:
        """Record a rollback attempt."""
        return self.record("rollback.attempt", actor, details, outcome, correlation_id=correlation_id)

    def record_secret_metadata_access(self, actor: str, secret_reference: str, metadata_fields: Iterable[str], outcome: str = "success", correlation_id: str | None = None) -> AuditEntry:
        """Record access to secret metadata without accepting a secret value."""
        if not isinstance(secret_reference, str) or not secret_reference.startswith("secret://"):
            raise ValueError("secret metadata audit requires a secret:// reference")
        details = {"secret_reference": secret_reference, "metadata_fields": list(metadata_fields), "value_accessed": False}
        return self.record("secret.metadata_access", actor, details, outcome, correlation_id=correlation_id)

    def entries(self) -> tuple[AuditEntry, ...]:
        """Return all entries in append order."""
        return tuple(self._entries)

    def query(self, event_type: str | None = None, actor: str | None = None, outcome: str | None = None) -> tuple[AuditEntry, ...]:
        """Filter entries by optional event dimensions."""
        return tuple(entry for entry in self._entries if (event_type is None or entry.event_type == event_type) and (actor is None or entry.actor == actor) and (outcome is None or entry.outcome == outcome))

    def verify_integrity(self) -> bool:
        """Verify hash chain integrity for all persisted entries."""
        previous = "GENESIS"
        for entry in self._entries:
            if entry.previous_hash != previous:
                raise AuditIntegrityError(f"audit chain predecessor mismatch at {entry.entry_id}")
            unsigned = {"entry_id": entry.entry_id, "timestamp": entry.timestamp, "event_type": entry.event_type, "actor": entry.actor, "outcome": entry.outcome, "details": entry.details, "previous_hash": entry.previous_hash, "source": entry.source, "correlation_id": entry.correlation_id}
            if self._hash(unsigned) != entry.entry_hash:
                raise AuditIntegrityError(f"audit entry hash mismatch at {entry.entry_id}")
            previous = entry.entry_hash
        return True

    def _append(self, entry: AuditEntry) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_dict(), sort_keys=True, default=str) + "\n")

    def _load(self) -> None:
        if not self.path.exists():
            return
        loaded: list[AuditEntry] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            loaded.append(AuditEntry(str(item["entry_id"]), str(item["timestamp"]), str(item["event_type"]), str(item["actor"]), str(item["outcome"]), dict(item.get("details", {})), str(item["previous_hash"]), str(item["entry_hash"]), str(item.get("source", "autonetarchitect")), item.get("correlation_id")))
        self._entries = loaded

    @staticmethod
    def _hash(unsigned: dict[str, Any]) -> str:
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
