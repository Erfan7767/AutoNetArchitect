"""Offline deprecated-command detection from governed data."""
from __future__ import annotations

import json
from pathlib import Path
import re

from .models import Severity, ValidationDiagnostic, ValidationStage


class DeprecatedCommandChecker:
    """Check only explicitly catalogued deprecations and avoid universal claims."""

    def __init__(self, data_path: str | Path | None = None) -> None:
        path = Path(data_path or (Path(__file__).parent.parent / "data" / "deprecated_commands.json"))
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.entries = payload.get("entries", [])

    def check(self, config_text: str, vendor: str, platform: str, platform_version: str | None = None) -> list[ValidationDiagnostic]:
        """Return warnings for matching, scoped deprecated commands."""
        diagnostics: list[ValidationDiagnostic] = []
        for number, line in enumerate(config_text.splitlines(), 1):
            stripped = line.strip()
            for entry in self.entries:
                if str(entry.get("vendor", "")).lower() != vendor.lower() or str(entry.get("platform", "")).lower() != platform.lower():
                    continue
                if re.search(str(entry.get("pattern", "")), stripped):
                    severity = Severity.WARNING if entry.get("severity", "warning") == "warning" else Severity.INFO
                    diagnostics.append(ValidationDiagnostic("DEPRECATED_COMMAND", f"Command is catalogued as deprecated or redundant: {stripped}", severity, ValidationStage.DEPRECATED, number, stripped, remediation=str(entry.get("replacement_command", "Confirm current vendor documentation.")), metadata={"deprecated_since_version": entry.get("deprecated_since_version"), "platform_version": platform_version}))
        return diagnostics
