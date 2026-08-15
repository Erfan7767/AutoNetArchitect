"""Shared conservative utilities for supported vendor parsers."""

from __future__ import annotations

import re
from typing import Any, ClassVar

from ..discovery_models import ConfidenceLevel, ParsedDevice


class VendorParser:
    """Base parser that never invents identity values from incomplete output."""

    vendor: ClassVar[str] = "unknown"
    parser_name: ClassVar[str] = "generic"
    platform: ClassVar[str] = "unknown"
    field_patterns: ClassVar[dict[str, tuple[str, ...]]] = {}
    observation_patterns: ClassVar[dict[str, tuple[str, ...]]] = {}

    def parse(self, output: str, evidence_hash: str = "") -> ParsedDevice:
        """Parse sanitized command output with explicit ambiguity tracking."""
        if not isinstance(output, str) or not output.strip():
            return ParsedDevice(self.parser_name, self.vendor, self.platform, "", "", "", "", confidence=ConfidenceLevel.UNKNOWN.value, evidence_hash=evidence_hash)
        extracted: dict[str, str] = {}
        ambiguous: list[str] = []
        for field_name, patterns in self.field_patterns.items():
            value, is_ambiguous = self._extract(output, patterns)
            extracted[field_name] = value
            if is_ambiguous:
                ambiguous.append(field_name)
        observations: dict[str, Any] = {}
        for field_name, patterns in self.observation_patterns.items():
            value, is_ambiguous = self._extract(output, patterns)
            if is_ambiguous:
                ambiguous.append(field_name)
            if value:
                observations[field_name] = value
        confidence = self._confidence(extracted, ambiguous)
        return ParsedDevice(
            parser_name=self.parser_name,
            vendor=self.vendor,
            platform=self.platform,
            model=extracted.get("model", ""),
            version=extracted.get("version", ""),
            serial=extracted.get("serial", ""),
            hostname=extracted.get("hostname", ""),
            observations=observations,
            confidence=confidence,
            ambiguous_fields=tuple(sorted(set(ambiguous))),
            evidence_hash=evidence_hash,
        )

    @staticmethod
    def _extract(output: str, patterns: tuple[str, ...]) -> tuple[str, bool]:
        """Return one normalized capture, or mark the field ambiguous."""
        candidates: list[str] = []
        for pattern in patterns:
            for match in re.finditer(pattern, output, flags=re.IGNORECASE | re.MULTILINE):
                value = match.group(1).strip().strip('"\'')
                if value and value not in candidates:
                    candidates.append(value)
        if len(candidates) == 1:
            return candidates[0], False
        if len(candidates) > 1:
            return "", True
        return "", False

    @staticmethod
    def _confidence(values: dict[str, str], ambiguous: list[str]) -> str:
        """Calculate confidence only from explicit field completeness rules."""
        if ambiguous:
            return ConfidenceLevel.AMBIGUOUS.value
        complete = sum(bool(values.get(field)) for field in ("model", "version", "serial", "hostname"))
        if complete == 4:
            return ConfidenceLevel.HIGH.value
        if complete >= 2:
            return ConfidenceLevel.MEDIUM.value
        if complete == 1:
            return ConfidenceLevel.LOW.value
        return ConfidenceLevel.UNKNOWN.value
