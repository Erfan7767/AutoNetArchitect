"""Administration page adapter for local project and UI state management."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate local administration action to the UI controller."""
    return controller.handle_page("admin", payload or {})
