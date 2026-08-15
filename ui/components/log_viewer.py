"""Secret-safe log and audit view model for the V1 UI shell."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ui.state_manager import mask_for_ui


@dataclass(frozen=True)
class LogViewer:
    """Read-only display model for audit or job entries."""

    entries: tuple[dict[str, Any], ...]
    source: str = "audit"

    @classmethod
    def from_entries(cls, entries: Iterable[Any], *, source: str = "audit") -> "LogViewer":
        """Normalize dataclass, mapping, or object entries into safe mappings."""
        normalized: list[dict[str, Any]] = []
        for entry in entries:
            if hasattr(entry, "to_dict") and callable(entry.to_dict):
                item = entry.to_dict()
            elif isinstance(entry, Mapping):
                item = dict(entry)
            else:
                item = {"value": str(entry)}
            normalized.append(dict(mask_for_ui(item)))
        return cls(entries=tuple(normalized), source=source)

    def filter(self, *, event_type: str | None = None, outcome: str | None = None, limit: int = 100) -> "LogViewer":
        """Return a bounded filtered view without modifying the source entries."""
        if limit < 1:
            raise ValueError("limit must be positive")
        selected = [entry for entry in self.entries if (event_type is None or entry.get("event_type") == event_type) and (outcome is None or entry.get("outcome") == outcome)]
        return LogViewer(entries=tuple(selected[-limit:]), source=self.source)

    def render(self) -> dict[str, Any]:
        """Return read-only safe log data."""
        return {"source": self.source, "entries": [dict(mask_for_ui(item)) for item in self.entries], "read_only": True}
