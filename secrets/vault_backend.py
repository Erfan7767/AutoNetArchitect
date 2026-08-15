"""V1 local encrypted vault backend for secret values."""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import os
from typing import Any


class VaultError(RuntimeError):
    """Base error for vault operations."""


class VaultLockedError(VaultError):
    """Raised when an operation requires an unlocked vault."""


class VaultIntegrityError(VaultError):
    """Raised when the encrypted vault cannot be authenticated or parsed."""


@dataclass(frozen=True)
class VaultConfig:
    """Non-secret vault cryptographic parameters."""

    version: int = 1
    kdf: str = "pbkdf2_hmac_sha256"
    iterations: int = 310_000
    key_length: int = 32
    salt_length: int = 16
    nonce_length: int = 12


class LocalEncryptedVaultBackend:
    """Store secret values in an authenticated encrypted JSON envelope."""

    def __init__(self, path: str | Path, config: VaultConfig | None = None) -> None:
        self.path = Path(path)
        self.config = config or VaultConfig()
        self._key: bytearray | None = None
        self._salt: bytes | None = None
        self._values: dict[str, str] = {}

    @property
    def is_unlocked(self) -> bool:
        """Return whether the backend currently holds an in-memory key."""
        return self._key is not None

    def initialize(self, master_password: str) -> None:
        """Create a new empty encrypted vault."""
        self._validate_master_password(master_password)
        if self.path.exists():
            raise VaultError(f"vault already exists: {self.path}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._salt = os.urandom(self.config.salt_length)
        self._key = bytearray(self._derive_key(master_password, self._salt))
        self._values = {}
        self._persist()

    def unlock(self, master_password: str) -> None:
        """Unlock and authenticate an existing vault."""
        self._validate_master_password(master_password)
        if not self.path.exists():
            raise VaultError("vault does not exist; initialize it first")
        envelope = self._read_envelope()
        salt = self._decode(envelope.get("salt"))
        nonce = self._decode(envelope.get("nonce"))
        ciphertext = self._decode(envelope.get("ciphertext"))
        iterations = int(envelope.get("iterations", self.config.iterations))
        key = self._derive_key(master_password, salt, iterations)
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            plaintext = AESGCM(key).decrypt(nonce, ciphertext, self._aad(envelope))
            values = json.loads(plaintext.decode("utf-8"))
        except Exception as exc:
            raise VaultIntegrityError("vault authentication failed or payload is invalid") from exc
        if not isinstance(values, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in values.items()):
            raise VaultIntegrityError("vault payload has an invalid value shape")
        self._salt = salt
        self._key = bytearray(key)
        self._values = dict(values)

    def lock(self) -> None:
        """Clear the in-memory key and plaintext values."""
        if self._key is not None:
            for index in range(len(self._key)):
                self._key[index] = 0
        self._key = None
        self._salt = None
        self._values = {}

    def put(self, secret_id: str, value: str) -> None:
        """Encrypt and persist one secret value."""
        self._require_unlocked()
        self._validate_id(secret_id)
        if not isinstance(value, str) or not value:
            raise ValueError("secret value must be a non-empty string")
        self._values[secret_id] = value
        self._persist()

    def get(self, secret_id: str) -> str:
        """Return one decrypted value only to the caller that requested it."""
        self._require_unlocked()
        self._validate_id(secret_id)
        try:
            return self._values[secret_id]
        except KeyError as exc:
            raise KeyError(f"secret not found: {secret_id}") from exc

    def delete(self, secret_id: str) -> None:
        """Delete one secret value and persist the new encrypted payload."""
        self._require_unlocked()
        self._values.pop(secret_id, None)
        self._persist()

    def exists(self, secret_id: str) -> bool:
        """Return whether a secret exists without returning its value."""
        self._require_unlocked()
        return secret_id in self._values

    def secret_ids(self) -> tuple[str, ...]:
        """Return deterministic secret IDs without exposing values."""
        self._require_unlocked()
        return tuple(sorted(self._values))

    def _persist(self) -> None:
        self._require_unlocked()
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        salt = self._salt or self._read_existing_salt() or os.urandom(self.config.salt_length)
        self._salt = salt
        nonce = os.urandom(self.config.nonce_length)
        envelope: dict[str, Any] = {
            "version": self.config.version,
            "kdf": self.config.kdf,
            "iterations": self.config.iterations,
            "key_length": self.config.key_length,
            "salt": self._encode(salt),
            "nonce": self._encode(nonce),
        }
        plaintext = json.dumps(self._values, sort_keys=True, separators=(",", ":")).encode("utf-8")
        envelope["ciphertext"] = self._encode(AESGCM(bytes(self._key)).encrypt(nonce, plaintext, self._aad(envelope)))
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(envelope, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def _read_existing_salt(self) -> bytes | None:
        if not self.path.exists():
            return None
        try:
            return self._decode(json.loads(self.path.read_text(encoding="utf-8")).get("salt"))
        except (OSError, ValueError, TypeError):
            return None

    def _read_envelope(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise VaultIntegrityError("vault envelope is not valid JSON") from exc
        if not isinstance(payload, dict) or payload.get("version") != self.config.version:
            raise VaultIntegrityError("unsupported vault envelope version")
        return payload

    def _require_unlocked(self) -> None:
        if self._key is None:
            raise VaultLockedError("vault is locked")

    @staticmethod
    def _validate_master_password(master_password: str) -> None:
        if not isinstance(master_password, str) or len(master_password) < 12:
            raise ValueError("master password must contain at least 12 characters")

    @staticmethod
    def _validate_id(secret_id: str) -> None:
        if not isinstance(secret_id, str) or not secret_id or "\\" in secret_id or any(part in {"", ".", ".."} for part in secret_id.split("/")):
            raise ValueError("secret ID must be a non-empty hierarchical identifier without traversal")

    @staticmethod
    def _derive_key(master_password: str, salt: bytes, iterations: int = 310_000) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", master_password.encode("utf-8"), salt, iterations, dklen=32)

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")

    @staticmethod
    def _decode(value: Any) -> bytes:
        if not isinstance(value, str):
            raise VaultIntegrityError("vault envelope has invalid base64 field")
        try:
            return base64.b64decode(value.encode("ascii"), validate=True)
        except (ValueError, TypeError) as exc:
            raise VaultIntegrityError("vault envelope has invalid base64 field") from exc

    @staticmethod
    def _aad(envelope: dict[str, Any]) -> bytes:
        authenticated = {key: envelope[key] for key in ("version", "kdf", "iterations", "key_length", "salt", "nonce") if key in envelope}
        return json.dumps(authenticated, sort_keys=True, separators=(",", ":")).encode("utf-8")
