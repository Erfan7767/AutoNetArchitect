"""Deployment page adapter; all deployment gates remain in orchestrators."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate deployment preparation or execution to the UI controller."""
    return controller.handle_page("deployment", payload or {})
