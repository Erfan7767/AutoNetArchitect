"""Cisco ios configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class IOSGenerator(BaseGenerator):
    """Generate Cisco ios artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("Cisco", "ios", "cisco/ios.j2", name or "IOSGenerator")
