"""Governed device profiling on top of sanitized discovery snapshots."""

from __future__ import annotations

from .discovery_models import (
    ConfidenceLevel,
    DeviceProfile,
    DiscoverySnapshot,
    DiscoveryStatus,
    ParsedDevice,
)
from .network_discovery import NetworkDiscovery


class DeviceProfiler:
    """Select a validated V1 parser and preserve its uncertainty markers."""

    def profile(self, snapshot: DiscoverySnapshot) -> DeviceProfile:
        """Profile a snapshot using all supplied command outputs."""
        parser = NetworkDiscovery.parser_for(snapshot.vendor) or NetworkDiscovery.parser_for(snapshot.platform)
        if parser is None:
            return DeviceProfile(
                device_id=snapshot.device_id,
                vendor=snapshot.vendor,
                platform=snapshot.platform,
                model=snapshot.model,
                version="",
                serial="",
                hostname="",
                parser_name="unsupported",
                status=DiscoveryStatus.UNSUPPORTED_VENDOR.value,
                confidence=ConfidenceLevel.UNKNOWN.value,
                safe_for_production=False,
                observations={},
                missing_inputs=("validated_vendor_parser",),
                evidence_hash=snapshot.evidence_hash,
            )
        parsed = self._parse_snapshot(parser, snapshot)
        status = DiscoveryStatus.COLLECTED.value
        if parsed.confidence == ConfidenceLevel.AMBIGUOUS.value:
            status = DiscoveryStatus.UNKNOWN_DEVICE.value
        elif parsed.confidence == ConfidenceLevel.UNKNOWN.value:
            status = DiscoveryStatus.UNKNOWN_DEVICE.value
        safe = parsed.confidence == ConfidenceLevel.HIGH.value and not parsed.unsupported_features
        missing = tuple(field for field in ("model", "version", "serial", "hostname") if not getattr(parsed, field))
        return DeviceProfile(
            device_id=snapshot.device_id,
            vendor=parsed.vendor,
            platform=parsed.platform or snapshot.platform,
            model=parsed.model or snapshot.model,
            version=parsed.version,
            serial=parsed.serial,
            hostname=parsed.hostname,
            parser_name=parsed.parser_name,
            status=status,
            confidence=parsed.confidence,
            safe_for_production=safe,
            observations=parsed.observations,
            ambiguous_fields=parsed.ambiguous_fields,
            unsupported_features=parsed.unsupported_features,
            missing_inputs=missing,
            evidence_hash=parsed.evidence_hash or snapshot.evidence_hash,
        )

    @staticmethod
    def _parse_snapshot(parser, snapshot: DiscoverySnapshot) -> ParsedDevice:
        """Parse command outputs in deterministic command order."""
        parsed_values: list[ParsedDevice] = [parser.parse(output, snapshot.evidence_hash) for _, output in sorted(snapshot.raw_outputs.items())]
        if not parsed_values:
            return parser.parse("", snapshot.evidence_hash)
        merged = parsed_values[0]
        for candidate in parsed_values[1:]:
            merged = DeviceProfiler._merge(merged, candidate)
        return merged

    @staticmethod
    def _merge(left: ParsedDevice, right: ParsedDevice) -> ParsedDevice:
        """Merge parser observations and mark conflicting identity fields ambiguous."""
        values: dict[str, str] = {}
        ambiguous = set(left.ambiguous_fields) | set(right.ambiguous_fields)
        for field in ("model", "version", "serial", "hostname"):
            left_value = getattr(left, field)
            right_value = getattr(right, field)
            if left_value and right_value and left_value != right_value:
                values[field] = ""
                ambiguous.add(field)
            else:
                values[field] = left_value or right_value
        complete = sum(bool(values[field]) for field in ("model", "version", "serial", "hostname"))
        confidence = ConfidenceLevel.AMBIGUOUS.value if ambiguous else ConfidenceLevel.HIGH.value if complete == 4 else ConfidenceLevel.MEDIUM.value if complete >= 2 else ConfidenceLevel.LOW.value if complete == 1 else ConfidenceLevel.UNKNOWN.value
        return ParsedDevice(
            parser_name=left.parser_name,
            vendor=left.vendor,
            platform=left.platform,
            model=values["model"],
            version=values["version"],
            serial=values["serial"],
            hostname=values["hostname"],
            observations=left.observations | right.observations,
            confidence=confidence,
            ambiguous_fields=tuple(sorted(ambiguous)),
            unsupported_features=tuple(sorted(set(left.unsupported_features) | set(right.unsupported_features))),
            evidence_hash=left.evidence_hash or right.evidence_hash,
        )
