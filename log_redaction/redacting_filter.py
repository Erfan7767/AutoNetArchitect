"""Mandatory redaction utilities for log messages and structured values."""
from __future__ import annotations

import logging
import re
from typing import Any


class RedactingFilter(logging.Filter):
    """Redact credentials, private keys, and sensitive key-value pairs."""

    REDACTED = "<REDACTED>"
    SENSITIVE_KEY_PATTERN = re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|client[_-]?secret|private[_-]?key|psk|community|shared[_-]?secret|master[_-]?password)")
    KEY_VALUE_PATTERN = re.compile(r"(?i)(\b(?:password|passwd|secret|token|api[_-]?key|client[_-]?secret|private[_-]?key|psk|community|shared[_-]?secret|master[_-]?password)\b\s*[:=]\s*)(?!secret://)([^\s,;]+)")
    AUTH_PATTERN = re.compile(r"(?i)(\b(?:authorization\s*:\s*bearer|basic|x-api-key)\s+)(?!secret://)([^\s]+)")
    PEM_PATTERN = re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", re.DOTALL)
    URL_CREDENTIAL_PATTERN = re.compile(r"(?i)(://[^/:\s]+:)([^@\s]+)(@)")

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact a LogRecord in-place before any handler formats it."""
        rendered = record.getMessage()
        record.msg = self.redact_text(rendered)
        record.args = ()
        return True

    @classmethod
    def redact_text(cls, value: str) -> str:
        """Redact sensitive text while preserving safe secret:// references."""
        if not isinstance(value, str):
            return cls.REDACTED
        references: dict[str, str] = {}
        def protect(match: re.Match[str]) -> str:
            token = f"__SECRET_REFERENCE_{len(references)}__"
            references[token] = match.group(0)
            return token
        result = re.sub(r"secret://[A-Za-z0-9._/-]+", protect, value)
        result = cls.PEM_PATTERN.sub(cls.REDACTED, result)
        result = cls.KEY_VALUE_PATTERN.sub(lambda match: match.group(1) + cls.REDACTED, result)
        result = cls.AUTH_PATTERN.sub(lambda match: match.group(1) + cls.REDACTED, result)
        result = cls.URL_CREDENTIAL_PATTERN.sub(lambda match: match.group(1) + cls.REDACTED + match.group(3), result)
        for token, reference in references.items():
            result = result.replace(token, reference)
        return result

    @classmethod
    def sanitize_value(cls, value: Any, key: str | None = None) -> Any:
        """Recursively sanitize structured data by sensitive key and value pattern."""
        if key is not None and cls.SENSITIVE_KEY_PATTERN.search(key):
            if isinstance(value, str) and value.startswith("secret://"):
                return value
            return cls.REDACTED
        if isinstance(value, str):
            return cls.redact_text(value)
        if isinstance(value, dict):
            return {str(item_key): cls.sanitize_value(item_value, str(item_key)) for item_key, item_value in value.items()}
        if isinstance(value, list):
            return [cls.sanitize_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls.sanitize_value(item) for item in value)
        return value
