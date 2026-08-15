"""Audit report generation for governance and operations review."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from .audit_trail import AuditEntry, AuditTrail


@dataclass(frozen=True)
class AuditReport:
    """Aggregated audit report with traceable entries."""

    generated_at: str
    total_entries: int
    by_event_type: dict[str, int]
    by_actor: dict[str, int]
    by_outcome: dict[str, int]
    entries: tuple[AuditEntry, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report for delivery or storage."""
        return {
            "generated_at": self.generated_at,
            "total_entries": self.total_entries,
            "by_event_type": dict(self.by_event_type),
            "by_actor": dict(self.by_actor),
            "by_outcome": dict(self.by_outcome),
            "entries": [entry.to_dict() for entry in self.entries],
        }

    def write_json(self, path: str | Path) -> Path:
        """Write a JSON report and return its path."""
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        return output


class AuditReporter:
    """Generate filtered, aggregate audit reports."""

    def __init__(self, trail: AuditTrail) -> None:
        self.trail = trail

    def generate(self, event_type: str | None = None, actor: str | None = None, outcome: str | None = None) -> AuditReport:
        """Generate an audit report from the verified trail."""
        from datetime import datetime, timezone
        entries = self.trail.query(event_type, actor, outcome)
        by_event: dict[str, int] = {}
        by_actor: dict[str, int] = {}
        by_outcome: dict[str, int] = {}
        for entry in entries:
            by_event[entry.event_type] = by_event.get(entry.event_type, 0) + 1
            by_actor[entry.actor] = by_actor.get(entry.actor, 0) + 1
            by_outcome[entry.outcome] = by_outcome.get(entry.outcome, 0) + 1
        return AuditReport(datetime.now(timezone.utc).isoformat(), len(entries), dict(sorted(by_event.items())), dict(sorted(by_actor.items())), dict(sorted(by_outcome.items())), entries)
