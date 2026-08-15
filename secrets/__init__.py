"""Secret management package with compatibility for Python's stdlib secrets API."""
from __future__ import annotations

import base64
import os
import random
from typing import Sequence, TypeVar

from .secret_manager import SecretManager, SecretMetadata
from .vault_backend import LocalEncryptedVaultBackend, VaultConfig, VaultError, VaultIntegrityError, VaultLockedError
from .rotation_policy import RotationDecision, RotationPolicy


_T = TypeVar("_T")
_SYSTEM_RANDOM = random.SystemRandom()


def token_bytes(nbytes: int | None = None) -> bytes:
    """Return cryptographically strong random bytes like the stdlib API."""
    length = 32 if nbytes is None else int(nbytes)
    if length < 0:
        raise ValueError("nbytes must be non-negative")
    return os.urandom(length)


def token_hex(nbytes: int | None = None) -> str:
    """Return a hexadecimal token compatible with Python's stdlib API."""
    return token_bytes(nbytes).hex()


def token_urlsafe(nbytes: int | None = None) -> str:
    """Return a URL-safe token compatible with Python's stdlib API."""
    return base64.urlsafe_b64encode(token_bytes(nbytes)).rstrip(b"=").decode("ascii")


def choice(sequence: Sequence[_T]) -> _T:
    """Return a cryptographically selected sequence member."""
    return _SYSTEM_RANDOM.choice(sequence)


def randbelow(exclusive_upper_bound: int) -> int:
    """Return a cryptographically selected integer below the bound."""
    if exclusive_upper_bound <= 0:
        raise ValueError("Upper bound must be positive")
    return _SYSTEM_RANDOM.randrange(exclusive_upper_bound)


__all__ = [
    "SecretManager",
    "SecretMetadata",
    "LocalEncryptedVaultBackend",
    "VaultConfig",
    "VaultError",
    "VaultIntegrityError",
    "VaultLockedError",
    "RotationDecision",
    "RotationPolicy",
    "token_bytes",
    "token_hex",
    "token_urlsafe",
    "choice",
    "randbelow",
]
