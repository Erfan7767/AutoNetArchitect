"""Approval and sign-off page formatting."""
from __future__ import annotations

from typing import Any


class ApprovalPageFormatter:
    """Create editable approval rows with no implied approval."""

    def build(self, roles: list[str] | None = None) -> list[dict[str, Any]]:
        """Return sign-off rows for supplied or standard roles."""
        selected = roles or ["Technical Reviewer", "Customer Approver", "Operations Owner"]
        return [{"role": role, "name": "PENDING", "signature": "PENDING", "date": "PENDING"} for role in selected]
