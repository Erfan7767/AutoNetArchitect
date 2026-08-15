"""Huawei vrp configuration generator."""
from __future__ import annotations

from config_generators.base_generator import BaseGenerator


class VRPGenerator(BaseGenerator):
    """Generate Huawei vrp artifacts through guarded exact-command rendering."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__("Huawei", "vrp", "huawei/vrp.j2", name or "VRPGenerator")
