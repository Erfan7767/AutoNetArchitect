"""Aruba aoscx configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class AOSCXGenerator(BaseGenerator):
    """Generate Aruba aoscx artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("Aruba", "aoscx", "aruba/aoscx.j2", name or "AOSCXGenerator")
