"""Questionnaire page adapter; business logic remains in orchestrators/services."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate questionnaire state handling to the UI controller."""
    return controller.handle_page("questionnaire", payload or {})
