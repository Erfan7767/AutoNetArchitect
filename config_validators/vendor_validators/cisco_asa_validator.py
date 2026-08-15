"""Cisco ASA offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class CiscoAsaValidator(BaseVendorValidator):
    """Validate Cisco ASA syntax and structure within the scoped grammar."""

    vendor = 'Cisco'
    platform = 'ASA'
    platform_key = 'cisco_asa'
    command_patterns = {"grammar": "data/cisco_asa_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
