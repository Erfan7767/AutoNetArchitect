"""PaloAlto panos configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class PANOSGenerator(BaseGenerator):
    """Generate PaloAlto panos artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("PaloAlto", "panos", "paloalto/panos.j2", name or "PANOSGenerator")
