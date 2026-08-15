"""Aruba AOS-CX offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class ArubaAoscxValidator(BaseVendorValidator):
    """Validate Aruba AOS-CX syntax and structure within the scoped grammar."""

    vendor = 'Aruba'
    platform = 'AOS-CX'
    platform_key = 'aruba_aoscx'
    command_patterns = {"grammar": "data/aruba_aoscx_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
