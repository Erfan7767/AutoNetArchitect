"""Fortinet fortigate configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class FortiGateGenerator(BaseGenerator):
    """Generate Fortinet fortigate artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("Fortinet", "fortigate", "fortinet/fortigate.j2", name or "FortiGateGenerator")
