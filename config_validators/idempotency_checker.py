"""Offline idempotency and re-application safety checks."""
from __future__ import annotations

import re

from .models import Severity, ValidationDiagnostic, ValidationStage


class IdempotencyChecker:
    """Detect commands that are destructive or likely non-idempotent."""

    def check(self, config_text: str, vendor: str, platform: str) -> list[ValidationDiagnostic]:
        """Return warnings/errors for reapplication hazards."""
        diagnostics: list[ValidationDiagnostic] = []
        seen: dict[str, int] = {}
        patterns = (
            (re.compile(r"(?i)^\s*(?:clear|reload|write\s+erase|erase\s+startup-config)\b"), Severity.CRITICAL, "DESTRUCTIVE_REAPPLICATION", "Remove destructive operational commands from configuration artifacts."),
            (re.compile(r"(?i)^\s*no\s+"), Severity.WARNING, "REMOVAL_ON_REAPPLICATION", "Confirm the removal is intentional and scoped to the target device."),
            (re.compile(r"(?i)\b(?:sequence|seq)\s+\d+\b"), Severity.WARNING, "ORDERED_SEQUENCE_REAPPLICATION", "Ensure sequence identifiers remain stable before a second application."),
        )
        for number, line in enumerate(config_text.splitlines(), 1):
            stripped = line.strip()
            if not stripped:
                continue
            normalized = re.sub(r"\s+", " ", stripped).lower()
            seen[normalized] = seen.get(normalized, 0) + 1
            for pattern, severity, code, remediation in patterns:
                if pattern.search(stripped):
                    diagnostics.append(ValidationDiagnostic(code, f"Potential non-idempotent command detected: {stripped}", severity, ValidationStage.IDEMPOTENCY, number, stripped, remediation=remediation))
                    break
        for command, count in seen.items():
            if count > 1 and (command.startswith("access-list ") or command.startswith("set ") or command.startswith("/")):
                diagnostics.append(ValidationDiagnostic("DUPLICATE_REAPPLICATION_LINE", f"The same command appears {count} times and may duplicate state on reapplication.", Severity.WARNING, ValidationStage.IDEMPOTENCY, command=config_text, remediation="Use an idempotent replace/set strategy or deduplicate the generated artifact.", metadata={"occurrences": count}))
        return diagnostics
