"""Palo Alto Networks PAN-OS offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class PaloaltoValidator(BaseVendorValidator):
    """Validate Palo Alto Networks PAN-OS syntax and structure within the scoped grammar."""

    vendor = 'Palo Alto Networks'
    platform = 'PAN-OS'
    platform_key = 'paloalto'
    command_patterns = {"grammar": "data/paloalto_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
