"""Safe, read-only network discovery collection primitives."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Mapping, Type

from .discovery_models import (
    DiscoveryCollectionResult,
    DiscoveryRequest,
    DiscoverySnapshot,
    DiscoveryStatus,
)
from .parsers import (
    ArubaParser,
    CiscoParser,
    FortinetParser,
    HuaweiParser,
    JuniperParser,
    MikroTikParser,
    PaloAltoParser,
)
from .parsers.parser_common import VendorParser


class NetworkDiscovery:
    """Collect supplied command outputs without opening sessions or changing devices.

    V1 deliberately accepts command output captured by an approved human or external
    read-only transport. It does not contain credential handling, command execution,
    configuration writes, or remediation behavior.
    """

    PARSER_TYPES: dict[str, Type[VendorParser]] = {
        "aruba": ArubaParser,
        "aoscx": ArubaParser,
        "cisco": CiscoParser,
        "ios": CiscoParser,
        "ios xe": CiscoParser,
        "ios_xe": CiscoParser,
        "nxos": CiscoParser,
        "asa": CiscoParser,
        "wlc": CiscoParser,
        "fortinet": FortinetParser,
        "fortigate": FortinetParser,
        "fortios": FortinetParser,
        "huawei": HuaweiParser,
        "vrp": HuaweiParser,
        "juniper": JuniperParser,
        "junos": JuniperParser,
        "mikrotik": MikroTikParser,
        "routeros": MikroTikParser,
        "paloalto": PaloAltoParser,
        "palo alto": PaloAltoParser,
        "panos": PaloAltoParser,
    }

    _SECRET_PATTERNS = (
        re.compile(r"(?im)^(\s*(?:password|secret|community|token|private[- ]key|shared[- ]secret)\s*[:=]\s*)\S+"),
        re.compile(r"(?im)(\b(?:password|secret|community|token|private[- ]key|shared[- ]secret)\s+)(\S+)"),
    )

    def collect(self, request: DiscoveryRequest, command_outputs: Mapping[str, str] | None) -> DiscoveryCollectionResult:
        """Create a sanitized snapshot from explicitly supplied read-only output."""
        if not request.read_only:
            return DiscoveryCollectionResult(DiscoveryStatus.BLOCKED_UNSAFE_MODE.value, request, None, reason="discovery request is not marked read_only")
        if not request.consent:
            return DiscoveryCollectionResult(DiscoveryStatus.BLOCKED_MISSING_HUMAN_DATA.value, request, None, required_human_inputs=("consent",), reason="human authorization for discovery is missing")
        if not request.device_id or not request.vendor:
            return DiscoveryCollectionResult(DiscoveryStatus.BLOCKED_MISSING_HUMAN_DATA.value, request, None, required_human_inputs=("device_id", "vendor"), reason="device identity is human-supplied and incomplete")
        if command_outputs is None or not command_outputs:
            return DiscoveryCollectionResult(DiscoveryStatus.BLOCKED_MISSING_HUMAN_DATA.value, request, None, required_human_inputs=("command_outputs",), reason="read-only command output must be supplied; no connection is attempted")
        sanitized_outputs: dict[str, str] = {}
        errors: list[str] = []
        for command, output in sorted(command_outputs.items()):
            if not isinstance(command, str) or not command.strip():
                errors.append("blank command label")
                continue
            if not isinstance(output, str):
                errors.append(f"non-text output for {command}")
                continue
            sanitized_outputs[command] = self.sanitize_output(output)
        if not sanitized_outputs:
            return DiscoveryCollectionResult(DiscoveryStatus.ERROR.value, request, None, reason="no valid text output was supplied")
        canonical = json.dumps(sanitized_outputs, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        evidence_hash = hashlib.sha256(canonical).hexdigest()
        snapshot = DiscoverySnapshot(
            device_id=request.device_id,
            vendor=request.vendor,
            platform=request.platform,
            model=request.model,
            source=request.source,
            acquired_at=datetime.now(timezone.utc).isoformat(),
            raw_outputs=sanitized_outputs,
            read_only=True,
            sanitized=True,
            evidence_hash=evidence_hash,
            errors=tuple(errors),
        )
        status = DiscoveryStatus.PARTIAL.value if errors else DiscoveryStatus.COLLECTED.value
        return DiscoveryCollectionResult(status, request, snapshot, reason="sanitized read-only snapshot created")

    @classmethod
    def parser_for(cls, vendor_or_platform: str) -> VendorParser | None:
        """Return a supported parser instance, or None for an unvalidated vendor."""
        key = str(vendor_or_platform).strip().lower()
        parser_type = cls.PARSER_TYPES.get(key)
        return parser_type() if parser_type else None

    @staticmethod
    def sanitize_output(output: str) -> str:
        """Redact common secret-bearing fields before hashing or parsing."""
        sanitized = output
        for pattern in NetworkDiscovery._SECRET_PATTERNS:
            sanitized = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]" if match.lastindex == 1 else f"{match.group(1)}[REDACTED]", sanitized)
        sanitized = re.sub(r"(?i)(secret://)([^\s,;]+)", r"\1[REFERENCE]", sanitized)
        return sanitized
