"""fortinet syntax rules."""
from __future__ import annotations

from config_validators.rules.common_rules import CommandRule, ParameterSpec

KNOWN_COMMANDS = {
    "rule_0": CommandRule(r"^config\\s+.+$", valid_modes=('global',), description='FortiOS config block'),
    "rule_1": CommandRule(r"^edit\\s+.+$", valid_modes=('global',), description='FortiOS edit block'),
    "rule_2": CommandRule(r"^set\\s+.+$", valid_modes=('global',), description='FortiOS set command'),
    "rule_3": CommandRule(r"^unset\\s+.+$", valid_modes=('global',), description='FortiOS unset command'),
    "rule_4": CommandRule(r"^append\\s+.+$", valid_modes=('global',), description='FortiOS append command'),
    "rule_5": CommandRule(r"^(?:next|end)$", valid_modes=('global',), description='FortiOS block transition'),
    "rule_6": CommandRule(r"^show(?:\\s+.+)?$", valid_modes=('global',), description='FortiOS show command'),
}
FORBIDDEN_PATTERNS = []
