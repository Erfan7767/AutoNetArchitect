"""Cisco IOS XE offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class CiscoIosXeValidator(BaseVendorValidator):
    """Validate Cisco IOS XE syntax and structure within the scoped grammar."""

    vendor = 'Cisco'
    platform = 'IOS XE'
    platform_key = 'cisco_ios_xe'
    command_patterns = {"grammar": "data/cisco_ios_xe_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
