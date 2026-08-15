"""Juniper Junos offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class JuniperJunosValidator(BaseVendorValidator):
    """Validate Juniper Junos syntax and structure within the scoped grammar."""

    vendor = 'Juniper'
    platform = 'Junos'
    platform_key = 'juniper_junos'
    command_patterns = {"grammar": "data/juniper_junos_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
