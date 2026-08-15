"""Cisco nxos configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class NXOSGenerator(BaseGenerator):
    """Generate Cisco nxos artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("Cisco", "nxos", "cisco/nxos.j2", name or "NXOSGenerator")
