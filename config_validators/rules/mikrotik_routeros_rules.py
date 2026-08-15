"""mikrotik_routeros syntax rules."""
from __future__ import annotations

from config_validators.rules.common_rules import CommandRule, ParameterSpec

KNOWN_COMMANDS = {
    "rule_0": CommandRule(r"^/[^\\s]+(?:/[^\\s]+)*\\s+(?:add|set|remove|print|export)(?:\\s+.*)?$", valid_modes=('global',), description='RouterOS path command'),
    "rule_1": CommandRule(r"^/[^\\s]+(?:/[^\\s]+)*$", valid_modes=('global',), description='RouterOS path'),
}
FORBIDDEN_PATTERNS = []
