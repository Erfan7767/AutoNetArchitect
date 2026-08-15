"""juniper_junos syntax rules."""
from __future__ import annotations

from config_validators.rules.common_rules import CommandRule, ParameterSpec

KNOWN_COMMANDS = {
    "rule_0": CommandRule(r"^(?:set|delete|deactivate|activate|rename|insert)\\s+.+$", valid_modes=('global',), description='Junos set command'),
    "rule_1": CommandRule(r"^(?:configure|commit|commit\\s+check|exit|rollback|show)(?:\\s+.*)?$", valid_modes=('global',), description='Junos command'),
    "rule_2": CommandRule(r"^[{};]$", valid_modes=('global',), description='Junos hierarchy delimiter'),
}
FORBIDDEN_PATTERNS = []
