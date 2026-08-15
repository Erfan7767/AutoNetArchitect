"""Equipment page adapter; equipment selection remains in the equipment layer."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate equipment workflow action to the UI controller."""
    return controller.handle_page("equipment", payload or {})
