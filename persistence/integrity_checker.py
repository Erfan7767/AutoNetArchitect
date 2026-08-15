"""Checksum and persistence integrity verification."""
from __future__ import annotations

import hashlib
import json
from typing import Any


class IntegrityError(RuntimeError):
    """Raised when persisted content fails integrity verification."""


class IntegrityChecker:
    """Verify deterministic SHA-256 checksums for project envelopes."""

    ALGORITHM = "sha256"

    @classmethod
    def canonical_json(cls, payload: dict[str, Any]) -> str:
        """Return canonical JSON used for checksum calculation."""
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

    @classmethod
    def checksum(cls, payload: dict[str, Any]) -> str:
        """Calculate a SHA-256 checksum for a JSON payload."""
        return hashlib.sha256(cls.canonical_json(payload).encode("utf-8")).hexdigest()

    @classmethod
    def envelope_checksum(cls, envelope: dict[str, Any]) -> str:
        """Calculate checksum over envelope fields excluding the stored checksum."""
        content = {key: value for key, value in envelope.items() if key != "checksum"}
        return cls.checksum(content)

    @classmethod
    def verify_envelope(cls, envelope: dict[str, Any]) -> bool:
        """Verify a persisted envelope and raise on mismatch."""
        stored = envelope.get("checksum")
        if not isinstance(stored, str) or not stored:
            raise IntegrityError("persisted envelope checksum is missing")
        calculated = cls.envelope_checksum(envelope)
        if not cls._constant_time_equal(stored, calculated):
            raise IntegrityError("persisted envelope checksum mismatch")
        if envelope.get("checksum_algorithm") != cls.ALGORITHM:
            raise IntegrityError("unsupported checksum algorithm")
        return True

    @staticmethod
    def _constant_time_equal(left: str, right: str) -> bool:
        if len(left) != len(right):
            return False
        difference = 0
        for left_char, right_char in zip(left, right):
            difference |= ord(left_char) ^ ord(right_char)
        return difference == 0
