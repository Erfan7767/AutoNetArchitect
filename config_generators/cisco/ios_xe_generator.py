"""Cisco ios_xe configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class IOSXEGenerator(BaseGenerator):
    """Generate Cisco ios_xe artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("Cisco", "ios_xe", "cisco/ios_xe.j2", name or "IOSXEGenerator")
