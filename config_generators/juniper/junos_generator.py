"""Juniper junos configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class JunosGenerator(BaseGenerator):
    """Generate Juniper junos artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("Juniper", "junos", "juniper/junos.j2", name or "JunosGenerator")
