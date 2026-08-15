"""Reports page adapter; report generation remains in the reports/export layers."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate reports workflow action to the UI controller."""
    return controller.handle_page("reports", payload or {})
