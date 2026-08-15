"""Cisco NX-OS offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class CiscoNxosValidator(BaseVendorValidator):
    """Validate Cisco NX-OS syntax and structure within the scoped grammar."""

    vendor = 'Cisco'
    platform = 'NX-OS'
    platform_key = 'cisco_nxos'
    command_patterns = {"grammar": "data/cisco_nxos_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
