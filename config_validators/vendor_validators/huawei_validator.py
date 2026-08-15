"""Huawei VRP offline validator."""
from __future__ import annotations

from .base_validator import BaseVendorValidator


class HuaweiValidator(BaseVendorValidator):
    """Validate Huawei VRP syntax and structure within the scoped grammar."""

    vendor = 'Huawei'
    platform = 'VRP'
    platform_key = 'huawei'
    command_patterns = {"grammar": "data/huawei_command_grammar.json"}
    hierarchy_rules = {"scope": ("model", "platform_version")}
    mode_transitions = {"exit": "parent", "end": "global"}
