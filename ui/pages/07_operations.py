"""Operations page adapter; operational actions are governed outside the UI."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate operations workflow action to the UI controller."""
    return controller.handle_page("operations", payload or {})
