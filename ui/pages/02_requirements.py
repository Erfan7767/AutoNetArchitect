"""Requirements page adapter; page code contains no requirements business logic."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate requirements workflow action to the UI controller."""
    return controller.handle_page("requirements", payload or {})
