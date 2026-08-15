"""paloalto syntax rules."""
from __future__ import annotations

from config_validators.rules.common_rules import CommandRule, ParameterSpec

KNOWN_COMMANDS = {
    "rule_0": CommandRule(r"^(?:set|delete|edit|move|clone|rename)\\s+.+$", valid_modes=('global',), description='PAN-OS set hierarchy'),
    "rule_1": CommandRule(r"^(?:configure|commit|exit|quit|show)(?:\\s+.*)?$", valid_modes=('global',), description='PAN-OS operational/config mode'),
}
FORBIDDEN_PATTERNS = []
