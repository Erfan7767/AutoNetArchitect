"""Compliance page adapter; technical assessment logic remains in compliance services."""
from __future__ import annotations

from typing import Any, Mapping


def render(controller: Any, payload: Mapping[str, Any] | None = None) -> Any:
    """Delegate compliance workflow action to the UI controller."""
    return controller.handle_page("compliance", payload or {})
