"""Cisco asa configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class ASAGenerator(BaseGenerator):
    """Generate Cisco asa artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("Cisco", "asa", "cisco/asa.j2", name or "ASAGenerator")
