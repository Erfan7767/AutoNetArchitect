"""Configuration page adapter; configuration generation remains outside UI."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate configuration workflow action to the UI controller."""
    return controller.handle_page("configs", payload or {})
