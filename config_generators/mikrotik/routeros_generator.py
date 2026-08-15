"""MikroTik routeros configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class RouterOSGenerator(BaseGenerator):
    """Generate MikroTik routeros artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("MikroTik", "routeros", "mikrotik/routeros.j2", name or "RouterOSGenerator")
