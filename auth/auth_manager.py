"""Local password authentication for AutoNetArchitect V1."""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

from .rbac import Principal, RBAC


class AuthenticationError(RuntimeError):
    """Raised when authentication or user management fails."""


@dataclass(frozen=True)
class UserRecord:
    """Persisted user record containing a password hash, never a password."""

    username: str
    salt: str
    password_hash: str
    iterations: int
    roles: tuple[str, ...]
    active: bool = True
    created_at: str = ""
    last_login_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize a user record without plaintext credentials."""
        return asdict(self) | {"roles": list(self.roles)}


class AuthManager:
    """Manage local users and authenticate principals against PBKDF2 hashes."""

    DEFAULT_ITERATIONS = 310_000

    def __init__(self, user_store_path: str | Path, rbac: RBAC | None = None, audit_trail: Any | None = None) -> None:
        self.user_store_path = Path(user_store_path)
        self.rbac = rbac or RBAC()
        self.audit_trail = audit_trail
        self._users: dict[str, UserRecord] = {}
        self._load()

    def create_user(self, username: str, password: str, roles: tuple[str, ...] = ("viewer",)) -> UserRecord:
        """Create a local user with a salted password hash."""
        self._validate_username(username)
        self._validate_password(password)
        if username in self._users:
            raise AuthenticationError("user already exists")
        normalized_roles = tuple(dict.fromkeys(roles))
        for role in normalized_roles:
            self.rbac.role(role)
        now = self._now()
        salt = os.urandom(16)
        record = UserRecord(username, self._encode(salt), self._encode(self._hash(password, salt, self.DEFAULT_ITERATIONS)), self.DEFAULT_ITERATIONS, normalized_roles, True, now, None)
        self._users[username] = record
        self._persist()
        self._audit("user.created", {"username": username, "roles": list(normalized_roles)})
        return record

    def authenticate(self, username: str, password: str) -> Principal:
        """Authenticate a user and return an RBAC principal."""
        record = self._users.get(username)
        if record is None or not record.active:
            self._audit("auth.login_failed", {"username": username, "reason": "unknown_or_inactive_user"})
            raise AuthenticationError("invalid username or password")
        salt = self._decode(record.salt)
        candidate = self._hash(password, salt, record.iterations)
        if not hmac.compare_digest(candidate, self._decode(record.password_hash)):
            self._audit("auth.login_failed", {"username": username, "reason": "invalid_password"})
            raise AuthenticationError("invalid username or password")
        updated = UserRecord(record.username, record.salt, record.password_hash, record.iterations, record.roles, record.active, record.created_at, self._now())
        self._users[username] = updated
        self._persist()
        self._audit("auth.login_success", {"username": username, "roles": list(record.roles)})
        return Principal(username, record.roles)

    def change_password(self, username: str, new_password: str) -> UserRecord:
        """Replace a password hash without exposing the new password."""
        self._validate_password(new_password)
        record = self._users.get(username)
        if record is None:
            raise AuthenticationError("user not found")
        salt = os.urandom(16)
        updated = UserRecord(record.username, self._encode(salt), self._encode(self._hash(new_password, salt, self.DEFAULT_ITERATIONS)), self.DEFAULT_ITERATIONS, record.roles, record.active, record.created_at, record.last_login_at)
        self._users[username] = updated
        self._persist()
        self._audit("user.password_changed", {"username": username})
        return updated

    def set_active(self, username: str, active: bool) -> UserRecord:
        """Enable or disable a local user."""
        record = self._users.get(username)
        if record is None:
            raise AuthenticationError("user not found")
        updated = UserRecord(record.username, record.salt, record.password_hash, record.iterations, record.roles, active, record.created_at, record.last_login_at)
        self._users[username] = updated
        self._persist()
        self._audit("user.status_changed", {"username": username, "active": active})
        return updated

    def get_user(self, username: str) -> UserRecord:
        """Return a persisted user record without plaintext credentials."""
        try:
            return self._users[username]
        except KeyError as exc:
            raise AuthenticationError("user not found") from exc

    def list_users(self) -> tuple[UserRecord, ...]:
        """List user records deterministically."""
        return tuple(self._users[key] for key in sorted(self._users))

    def _load(self) -> None:
        if not self.user_store_path.exists():
            return
        payload = json.loads(self.user_store_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise AuthenticationError("user store must be a JSON object")
        self._users = {username: UserRecord(username, str(item["salt"]), str(item["password_hash"]), int(item["iterations"]), tuple(str(role) for role in item.get("roles", [])), bool(item.get("active", True)), str(item.get("created_at", "")), item.get("last_login_at")) for username, item in payload.items()}

    def _persist(self) -> None:
        self.user_store_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {username: record.to_dict() for username, record in sorted(self._users.items())}
        temporary = self.user_store_path.with_suffix(self.user_store_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.user_store_path)

    def _audit(self, event_type: str, details: dict[str, Any]) -> None:
        if self.audit_trail is not None:
            self.audit_trail.record(event_type, "system", details, outcome="success" if not event_type.endswith("failed") else "failure")

    @staticmethod
    def _hash(password: str, salt: bytes, iterations: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")

    @staticmethod
    def _decode(value: str) -> bytes:
        return base64.b64decode(value.encode("ascii"), validate=True)

    @staticmethod
    def _validate_username(username: str) -> None:
        if not isinstance(username, str) or not username or len(username) > 128 or any(character.isspace() for character in username):
            raise ValueError("username must be non-empty, bounded, and whitespace-free")

    @staticmethod
    def _validate_password(password: str) -> None:
        if not isinstance(password, str) or len(password) < 12:
            raise ValueError("password must contain at least 12 characters")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
