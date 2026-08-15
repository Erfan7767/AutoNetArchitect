"""Secret lifecycle service over an encrypted vault and separate metadata store."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

from .vault_backend import LocalEncryptedVaultBackend


@dataclass(frozen=True)
class SecretMetadata:
    """Non-secret metadata stored separately from the encrypted value."""

    secret_id: str
    purpose: str
    owner: str
    classification: str = "confidential"
    created_at: str = ""
    last_rotated_at: str = ""
    expires_at: str | None = None
    rotation_interval_days: int = 90
    version: int = 1
    tags: tuple[str, ...] = ()
    source_of_truth: str = "human_supplied"

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata without a secret value."""
        return asdict(self) | {"tags": list(self.tags)}


class SecretManager:
    """Manage secret references while keeping values inside the encrypted backend."""

    REFERENCE_PREFIX = "secret://"

    def __init__(self, backend: LocalEncryptedVaultBackend, metadata_path: str | Path) -> None:
        self.backend = backend
        self.metadata_path = Path(metadata_path)
        self._metadata: dict[str, SecretMetadata] = {}
        self._load_metadata()

    def initialize(self, master_password: str) -> None:
        """Initialize the encrypted backend and empty metadata registry."""
        self.backend.initialize(master_password)
        self._metadata = {}
        self._persist_metadata()

    def unlock(self, master_password: str) -> None:
        """Unlock the backend for controlled value operations."""
        self.backend.unlock(master_password)
        self._load_metadata()

    def lock(self) -> None:
        """Lock the backend and remove decrypted values from memory."""
        self.backend.lock()

    def put(self, secret_id: str, value: str, purpose: str, owner: str, classification: str = "confidential", rotation_interval_days: int = 90, tags: tuple[str, ...] = (), source_of_truth: str = "human_supplied", expires_at: str | None = None) -> SecretMetadata:
        """Create or replace a value and record only non-secret metadata."""
        self._require_unlocked()
        now = self._now()
        previous = self._metadata.get(secret_id)
        version = previous.version + 1 if previous else 1
        self.backend.put(secret_id, value)
        metadata = SecretMetadata(secret_id, purpose, owner, classification, previous.created_at if previous else now, now, expires_at, rotation_interval_days, version, tuple(tags), source_of_truth)
        self._metadata[secret_id] = metadata
        self._persist_metadata()
        return metadata

    def rotate(self, secret_id: str, new_value: str) -> SecretMetadata:
        """Rotate a secret without changing its stable reference."""
        self._require_unlocked()
        current = self.metadata(secret_id)
        return self.put(secret_id, new_value, current.purpose, current.owner, current.classification, current.rotation_interval_days, current.tags, current.source_of_truth, current.expires_at)

    def resolve(self, reference: str) -> str:
        """Resolve a secret:// reference; raw values are never accepted as references."""
        self._require_unlocked()
        secret_id = self.parse_reference(reference)
        if secret_id not in self._metadata:
            raise KeyError(f"secret metadata not found: {secret_id}")
        return self.backend.get(secret_id)

    def metadata(self, secret_id: str) -> SecretMetadata:
        """Return metadata only."""
        try:
            return self._metadata[secret_id]
        except KeyError as exc:
            raise KeyError(f"secret metadata not found: {secret_id}") from exc

    def list_metadata(self) -> tuple[SecretMetadata, ...]:
        """List metadata deterministically without exposing values."""
        return tuple(self._metadata[key] for key in sorted(self._metadata))

    def delete(self, secret_id: str) -> None:
        """Delete a value and its metadata."""
        self._require_unlocked()
        self.backend.delete(secret_id)
        self._metadata.pop(secret_id, None)
        self._persist_metadata()

    @classmethod
    def reference(cls, secret_id: str) -> str:
        """Build a stable reference accepted by generators and log redactors."""
        if not secret_id or "\\" in secret_id or any(part in {"", ".", ".."} for part in secret_id.split("/")):
            raise ValueError("secret ID must be hierarchical and traversal-safe")
        return f"{cls.REFERENCE_PREFIX}{secret_id}"

    @classmethod
    def parse_reference(cls, reference: str) -> str:
        """Parse a secret reference and reject inline values."""
        if not isinstance(reference, str) or not reference.startswith(cls.REFERENCE_PREFIX):
            raise ValueError("only secret:// references can be resolved")
        secret_id = reference[len(cls.REFERENCE_PREFIX):]
        if not secret_id or "\\" in secret_id or any(part in {"", ".", ".."} for part in secret_id.split("/")):
            raise ValueError("invalid secret reference")
        return secret_id

    def _require_unlocked(self) -> None:
        if not self.backend.is_unlocked:
            raise RuntimeError("secret manager is locked")

    def _load_metadata(self) -> None:
        if not self.metadata_path.exists():
            self._metadata = {}
            return
        payload = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("metadata store must be a JSON object")
        loaded: dict[str, SecretMetadata] = {}
        for secret_id, item in payload.items():
            if not isinstance(item, dict) or "value" in item or "secret" in item:
                raise ValueError("secret value cannot be stored in metadata")
            loaded[secret_id] = SecretMetadata(secret_id=secret_id, purpose=str(item.get("purpose", "")), owner=str(item.get("owner", "")), classification=str(item.get("classification", "confidential")), created_at=str(item.get("created_at", "")), last_rotated_at=str(item.get("last_rotated_at", "")), expires_at=item.get("expires_at"), rotation_interval_days=int(item.get("rotation_interval_days", 90)), version=int(item.get("version", 1)), tags=tuple(str(tag) for tag in item.get("tags", [])), source_of_truth=str(item.get("source_of_truth", "human_supplied")))
        self._metadata = loaded

    def _persist_metadata(self) -> None:
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {secret_id: metadata.to_dict() for secret_id, metadata in sorted(self._metadata.items())}
        temporary = self.metadata_path.with_suffix(self.metadata_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.metadata_path)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
