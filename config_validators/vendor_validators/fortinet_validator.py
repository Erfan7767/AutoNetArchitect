"""Fortinet FortiOS offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class FortinetValidator(BaseVendorValidator):
    """Validate Fortinet FortiOS syntax and structure within the scoped grammar."""

    vendor = 'Fortinet'
    platform = 'FortiOS'
    platform_key = 'fortinet'
    command_patterns = {"grammar": "data/fortinet_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
