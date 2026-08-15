"""Cisco WLC offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class CiscoWlcValidator(BaseVendorValidator):
    """Validate Cisco WLC syntax and structure within the scoped grammar."""

    vendor = 'Cisco'
    platform = 'WLC'
    platform_key = 'cisco_wlc'
    command_patterns = {"grammar": "data/cisco_wlc_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
