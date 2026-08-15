"""Cisco IOS offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class CiscoIosValidator(BaseVendorValidator):
    """Validate Cisco IOS syntax and structure within the scoped grammar."""

    vendor = 'Cisco'
    platform = 'IOS'
    platform_key = 'cisco_ios'
    command_patterns = {"grammar": "data/cisco_ios_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
