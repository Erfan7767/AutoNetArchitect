"""Immutable local history for every change lifecycle event."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence

from log_redaction.redacting_filter import RedactingFilter


@dataclass(frozen=True)
class ChangeHistoryEntry:
    """One append-only history event."""

    history_id: str
    change_id: str
    event_type: str
    actor: str
    timestamp: str
    details: dict[str, Any]
    previous_hash: str
    entry_hash: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize history entry."""
        return asdict(self)


class ChangeHistory:
    """Maintain an in-memory hash chain and query index for V1."""

    def __init__(self) -> None:
        """Create an empty history ledger."""
        self._entries: list[ChangeHistoryEntry] = []

    def record(self, change_id: str, event_type: str, actor: str, details: Mapping[str, Any] | None = None) -> ChangeHistoryEntry:
        """Append a sanitized immutable event."""
        if not change_id or not event_type or not actor:
            raise ValueError("change_id, event_type, and actor are required")
        sanitized = RedactingFilter.sanitize_value(dict(details or {}))
        if not isinstance(sanitized, dict):
            raise ValueError("history details must remain a mapping")
        timestamp = datetime.now(timezone.utc).isoformat()
        history_id = f"{change_id}:history:{len(self._entries) + 1:06d}"
        previous = self._entries[-1].entry_hash if self._entries else "GENESIS"
        unsigned = {"history_id": history_id, "change_id": change_id, "event_type": event_type, "actor": actor, "timestamp": timestamp, "details": sanitized, "previous_hash": previous}
        entry_hash = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
        entry = ChangeHistoryEntry(history_id, change_id, event_type, actor, timestamp, sanitized, previous, entry_hash)
        self._entries.append(entry)
        return entry

    def entries(self, change_id: str | None = None) -> tuple[ChangeHistoryEntry, ...]:
        """Return history entries, optionally filtered by change."""
        return tuple(entry for entry in self._entries if change_id is None or entry.change_id == change_id)

    def query(self, *, device_id: str | None = None, service_id: str | None = None, status: str | None = None, requester: str | None = None, change_type: str | None = None) -> tuple[ChangeHistoryEntry, ...]:
        """Search sanitized history details by common dimensions."""
        result = []
        for entry in self._entries:
            details = entry.details
            if device_id and device_id not in str(details.get("device_id", details.get("affected_devices", ""))):
                continue
            if service_id and service_id not in str(details.get("service_id", details.get("affected_services", ""))):
                continue
            if status and status != str(details.get("status", "")):
                continue
            if requester and requester != str(details.get("requester", "")):
                continue
            if change_type and change_type != str(details.get("change_type", "")):
                continue
            result.append(entry)
        return tuple(result)

    def verify_integrity(self) -> bool:
        """Verify the local hash chain."""
        previous = "GENESIS"
        for entry in self._entries:
            if entry.previous_hash != previous:
                return False
            unsigned = {"history_id": entry.history_id, "change_id": entry.change_id, "event_type": entry.event_type, "actor": entry.actor, "timestamp": entry.timestamp, "details": entry.details, "previous_hash": entry.previous_hash}
            expected = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
            if expected != entry.entry_hash:
                return False
            previous = entry.entry_hash
        return True
