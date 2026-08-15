"""Secret-safe and level-aware redaction for documentation content."""
from __future__ import annotations

import hashlib
import ipaddress
import re
from typing import Any

from .doc_models import RedactionLevel


class DocRedactionEngine:
    """Recursively redact secrets and optionally sensitive infrastructure identifiers."""

    _secret_key = re.compile(r"(password|passwd|secret|token|private[_ -]?key|community|credential|api[_ -]?key)", re.IGNORECASE)
    _secret_ref = re.compile(r"secret://[^\s,;]+", re.IGNORECASE)
    _serial_key = re.compile(r"serial", re.IGNORECASE)
    _hostname_key = re.compile(r"hostname|device_name|host", re.IGNORECASE)

    def redact(self, value: Any, level: RedactionLevel | str) -> tuple[Any, list[str], bool]:
        """Return a redacted copy, findings, and whether redaction was applied."""
        selected = RedactionLevel(level)
        findings: list[str] = []
        redacted = self._walk(value, selected, findings, key_hint="")
        return redacted, findings, bool(findings)

    def _walk(self, value: Any, level: RedactionLevel, findings: list[str], key_hint: str) -> Any:
        """Recursively traverse mappings, sequences, and scalar values."""
        if isinstance(value, dict):
            return {str(key): self._walk(item, level, findings, str(key)) for key, item in value.items()}
        if isinstance(value, list):
            return [self._walk(item, level, findings, key_hint) for item in value]
        if isinstance(value, tuple):
            return tuple(self._walk(item, level, findings, key_hint) for item in value)
        if self._secret_key.search(key_hint):
            findings.append(f"secret field redacted: {key_hint}")
            return "[REDACTED]"
        if isinstance(value, str):
            return self._redact_text(value, level, findings)
        return value

    def _redact_text(self, text: str, level: RedactionLevel, findings: list[str]) -> str:
        """Redact secret references or sensitive patterns in text."""
        output = self._secret_ref.sub(self._record_replacement(findings, "secret reference"), text)
        if level == RedactionLevel.STRICT:
            output = self._mask_ips(output, findings)
            output = self._hash_sensitive_labels(output, findings)
        return output

    @staticmethod
    def _record_replacement(findings: list[str], kind: str):
        """Create a regex replacement callback with a finding."""
        def replace(match: re.Match[str]) -> str:
            findings.append(f"{kind} redacted")
            return "[REDACTED]"
        return replace

    @staticmethod
    def _mask_ips(text: str, findings: list[str]) -> str:
        """Mask IPv4 and IPv6 addresses while retaining enough context for documentation."""
        tokens = re.findall(r"(?<![\w:])(?:\d{1,3}\.){3}\d{1,3}(?![\w:])|(?<![\w:])[0-9a-fA-F:]{3,39}:[0-9a-fA-F:]+(?![\w:])", text)
        output = text
        for token in tokens:
            try:
                address = ipaddress.ip_address(token)
            except ValueError:
                continue
            replacement = "x.x.x.x" if address.version == 4 else "xxxx::xxxx"
            output = output.replace(token, replacement)
            findings.append("network address masked under strict policy")
        return output

    @staticmethod
    def _hash_sensitive_labels(text: str, findings: list[str]) -> str:
        """Hash common device labels and serial-like values only when explicitly marked."""
        patterns = [
            (re.compile(r"(?i)(serial(?:\s*number)?\s*[:=]\s*)([A-Za-z0-9._-]+)"), "serial"),
            (re.compile(r"(?i)(hostname|device_name|host\s*[:=]\s*)([:=\s]+)([A-Za-z0-9._-]+)"), "label"),
        ]
        output = text
        for pattern, kind in patterns:
            def replace(match: re.Match[str], kind_value: str = kind) -> str:
                raw = match.group(match.lastindex or 1)
                digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8].upper()
                findings.append(f"{kind_value} hashed under strict policy")
                if kind_value == "serial":
                    return f"{match.group(1)}SERIAL-{digest}"
                return f"{match.group(1)}{match.group(2)}Device-{digest}"
            output = pattern.sub(replace, output)
        return output
