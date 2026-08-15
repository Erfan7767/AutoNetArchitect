"""Deprecation tracking for changed knowledge."""
from __future__ import annotations
from datetime import datetime, timezone
class DeprecationTracker:
    """Track deprecation reasons and replacements."""
    def __init__(self) -> None: self.records: dict[str, dict[str, object]] = {}
    def deprecate(self, item: object, reason: str, replacement_id: str | None = None) -> dict[str, object]:
        """Mark an item deprecated with an auditable reason."""
        item.publication_state = "deprecated"; record = {"item_id": item.item_id, "reason": reason, "replacement_id": replacement_id, "at": datetime.now(timezone.utc).isoformat()}; self.records[item.item_id] = record; return record
