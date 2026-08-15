"""Local session lifecycle management with expiry and revocation."""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Any

from .rbac import Principal


class SessionError(RuntimeError):
    """Raised for invalid, expired, or revoked sessions."""


@dataclass(frozen=True)
class SessionRecord:
    """Persisted session metadata; the token is represented only by its map key."""

    session_id: str
    username: str
    roles: tuple[str, ...]
    created_at: str
    expires_at: str
    last_seen_at: str
    revoked: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize session metadata."""
        return asdict(self) | {"roles": list(self.roles)}


class SessionManager:
    """Create, validate, touch, revoke, and clean up local sessions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._sessions: dict[str, SessionRecord] = {}
        self._load()

    def create(self, principal: Principal, ttl_seconds: int = 3600) -> SessionRecord:
        """Create a high-entropy opaque session token."""
        if ttl_seconds <= 0 or ttl_seconds > 86400:
            raise ValueError("ttl_seconds must be between 1 and 86400")
        now = datetime.now(timezone.utc)
        session_id = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii").rstrip("=")
        record = SessionRecord(session_id, principal.username, tuple(principal.roles), now.isoformat(), (now + timedelta(seconds=ttl_seconds)).isoformat(), now.isoformat(), False)
        self._sessions[session_id] = record
        self._persist()
        return record

    def validate(self, session_id: str, now: datetime | None = None) -> Principal:
        """Validate a session token and return its principal."""
        record = self._get(session_id)
        if record.revoked:
            raise SessionError("session is revoked")
        now = now or datetime.now(timezone.utc)
        if now >= self._parse(record.expires_at):
            self._sessions[session_id] = SessionRecord(record.session_id, record.username, record.roles, record.created_at, record.expires_at, record.last_seen_at, True)
            self._persist()
            raise SessionError("session has expired")
        self.touch(session_id, now)
        return Principal(record.username, record.roles, record.session_id)

    def touch(self, session_id: str, now: datetime | None = None) -> SessionRecord:
        """Update last-seen time without extending the original expiry."""
        record = self._get(session_id)
        if record.revoked:
            raise SessionError("session is revoked")
        now = now or datetime.now(timezone.utc)
        updated = SessionRecord(record.session_id, record.username, record.roles, record.created_at, record.expires_at, now.isoformat(), record.revoked)
        self._sessions[session_id] = updated
        self._persist()
        return updated

    def revoke(self, session_id: str) -> None:
        """Revoke one session."""
        record = self._get(session_id)
        self._sessions[session_id] = SessionRecord(record.session_id, record.username, record.roles, record.created_at, record.expires_at, record.last_seen_at, True)
        self._persist()

    def revoke_user(self, username: str) -> int:
        """Revoke all sessions belonging to a username."""
        count = 0
        for session_id, record in list(self._sessions.items()):
            if record.username == username and not record.revoked:
                self._sessions[session_id] = SessionRecord(record.session_id, record.username, record.roles, record.created_at, record.expires_at, record.last_seen_at, True)
                count += 1
        if count:
            self._persist()
        return count

    def cleanup(self, now: datetime | None = None) -> int:
        """Remove expired or revoked sessions from the local store."""
        now = now or datetime.now(timezone.utc)
        before = len(self._sessions)
        self._sessions = {session_id: record for session_id, record in self._sessions.items() if not record.revoked and now < self._parse(record.expires_at)}
        removed = before - len(self._sessions)
        if removed:
            self._persist()
        return removed

    def list_metadata(self) -> tuple[SessionRecord, ...]:
        """List session metadata without exposing additional token material."""
        return tuple(sorted(self._sessions.values(), key=lambda record: record.session_id))

    def _get(self, session_id: str) -> SessionRecord:
        if not isinstance(session_id, str) or not session_id:
            raise SessionError("session ID is required")
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise SessionError("session not found") from exc

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise SessionError("session store must be a JSON object")
        self._sessions = {session_id: SessionRecord(session_id, str(item["username"]), tuple(str(role) for role in item.get("roles", [])), str(item["created_at"]), str(item["expires_at"]), str(item["last_seen_at"]), bool(item.get("revoked", False))) for session_id, item in payload.items()}

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {session_id: record.to_dict() for session_id, record in sorted(self._sessions.items())}
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    @staticmethod
    def _parse(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
