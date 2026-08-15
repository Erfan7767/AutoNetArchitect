"""Design page adapter; design decisions are produced outside the UI layer."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate the design action to the UI controller."""
    return controller.handle_page("design", payload or {})
