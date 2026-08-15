"""MikroTik RouterOS offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class MikrotikRouterosValidator(BaseVendorValidator):
    """Validate MikroTik RouterOS syntax and structure within the scoped grammar."""

    vendor = 'MikroTik'
    platform = 'RouterOS'
    platform_key = 'mikrotik_routeros'
    command_patterns = {"grammar": "data/mikrotik_routeros_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
