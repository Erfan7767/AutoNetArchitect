"""Revision history formatting."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class RevisionHistoryFormatter:
    """Normalize supplied revision history without creating approvals."""

    def format(self, history: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        """Return supplied rows or an explicit pending row."""
        if history:
            return [dict(item) for item in history]
        return [{"revision": "1.0", "date": datetime.now(timezone.utc).date().isoformat(), "change": "PENDING: approval history not supplied", "approved_by": "PENDING"}]
