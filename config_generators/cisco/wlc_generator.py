"""Cisco wlc configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class WLCGenerator(BaseGenerator):
    """Generate Cisco wlc artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("Cisco", "wlc", "cisco/wlc.j2", name or "WLCGenerator")
