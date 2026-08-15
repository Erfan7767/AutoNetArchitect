"""Coverage reporting for offline syntax and semantics validation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CoverageRecord, CoverageStatus, ValidationLineResult


class CoverageTracker:
    """Track exact coverage and make uncovered command scope explicit."""

    def __init__(self, coverage_path: str | Path | None = None) -> None:
        path = Path(coverage_path or (Path(__file__).parent.parent / "data" / "validation_coverage_map.json"))
        self.payload = json.loads(path.read_text(encoding="utf-8"))

    def from_line_results(self, vendor: str, platform: str, results: list[ValidationLineResult]) -> CoverageRecord:
        """Aggregate line-level coverage for one config."""
        command_lines = [result for result in results if result.line.strip() and not result.line.strip().startswith(("!", "#"))]
        validated = sum(result.coverage_status is CoverageStatus.VALIDATED for result in command_lines)
        partial = tuple(dict.fromkeys(result.line.strip() for result in command_lines if result.coverage_status is CoverageStatus.PARTIALLY_VALIDATED))
        uncovered = tuple(dict.fromkeys(result.line.strip() for result in command_lines if result.coverage_status is CoverageStatus.NOT_COVERED))
        return CoverageRecord(vendor, platform, len(command_lines), validated, partial, uncovered)

    def vendor_record(self, vendor: str, platform: str) -> CoverageRecord:
        """Return static grammar coverage metadata."""
        key = f"{vendor}_{platform}".lower().replace(" ", "_").replace("-", "_")
        aliases = {"cisco_nx_os": "cisco_nxos", "fortinet_fortios": "fortinet", "palo_alto_networks_pan_os": "paloalto", "aruba_aos_cx": "aruba_aoscx"}
        key = aliases.get(key, key)
        item: dict[str, Any] = self.payload.get("vendor_coverage", {}).get(key, {})
        return CoverageRecord(vendor, platform, int(item.get("total_known_commands", 0)), int(item.get("validated_commands", 0)), tuple(item.get("partially_covered", [])), tuple(item.get("uncovered_commands", [])))

    def report(self, vendor: str, platform: str, results: list[ValidationLineResult]) -> dict[str, Any]:
        """Return a JSON-safe coverage report."""
        record = self.from_line_results(vendor, platform, results)
        return {"vendor": vendor, "platform": platform, "total_known_commands": record.total_known_commands, "validated_commands": record.validated_commands, "coverage_percentage": record.coverage_percentage, "partially_covered": list(record.partially_covered), "uncovered_commands": list(record.uncovered_commands), "coverage_claim": "validated means syntax plus semantic checks; partial means syntax only; not_covered means no grammar match"}
