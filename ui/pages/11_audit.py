"""Read-only audit page adapter with secret-safe filtering."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate audit viewing to the UI controller."""
    return controller.handle_page("audit", payload or {})
