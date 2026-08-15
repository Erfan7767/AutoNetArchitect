"""Offline grammar-driven command syntax validation."""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .models import CoverageStatus, Severity, ValidationDiagnostic, ValidationLineResult, ValidationStage
from .rules.common_rules import FORBIDDEN_PATTERNS, CommandRule, ParameterSpec, VALIDATORS


class SyntaxRuleEngine:
    """Validate covered command prefixes and explicitly report uncovered syntax."""

    def __init__(self, grammar_root: str | Path | None = None) -> None:
        self.grammar_root = Path(grammar_root or (Path(__file__).parent.parent / "data"))
        self._rules: dict[str, tuple[CommandRule, ...]] = {}
        self._load_grammars()

    @staticmethod
    def platform_key(vendor: str, platform: str) -> str:
        """Normalize vendor/platform to grammar filename key."""
        value = f"{vendor}_{platform}".lower().replace(" ", "_").replace("-", "_").replace("/", "_")
        aliases = {
            "cisco_ios_xe": "cisco_ios_xe",
            "cisco_ios": "cisco_ios",
            "cisco_nx_os": "cisco_nxos",
            "cisco_nxos": "cisco_nxos",
            "cisco_asa": "cisco_asa",
            "cisco_wlc": "cisco_wlc",
            "palo_alto_networks_pan_os": "paloalto",
            "paloalto_panos": "paloalto",
            "fortinet_fortios": "fortinet",
            "huawei_vrp": "huawei",
            "aruba_aos_cx": "aruba_aoscx",
            "aruba_aoscx": "aruba_aoscx",
            "juniper_junos": "juniper_junos",
            "mikrotik_routeros": "mikrotik_routeros",
        }
        return aliases.get(value, value)

    def _load_grammars(self) -> None:
        """Load all available JSON grammars."""
        for path in self.grammar_root.glob("*_command_grammar.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            rules: list[CommandRule] = []
            for item in payload.get("rules", []):
                specs = tuple(ParameterSpec(str(spec["name"]), str(spec.get("type", "string")), bool(spec.get("required", True)), tuple(str(choice) for choice in spec.get("choices", [])), spec.get("min"), spec.get("max")) for spec in item.get("parameter_specs", []))
                rules.append(CommandRule(str(item["pattern"]), specs, tuple(str(mode) for mode in item.get("valid_modes", ["global"])), False, item.get("min_version"), CoverageStatus(str(item.get("coverage_status", "validated"))), str(item.get("description", ""))))
            self._rules[path.name.removesuffix("_command_grammar.json")] = tuple(rules)

    def rules_for(self, vendor: str, platform: str) -> tuple[CommandRule, ...]:
        """Return loaded rules for a vendor/platform."""
        return self._rules.get(self.platform_key(vendor, platform), ())

    @staticmethod
    def _mode_transition(line: str, current: str) -> str:
        stripped = line.strip()
        if stripped in {"exit", "quit"}:
            return "global" if current == "global" else "parent"
        if stripped in {"end", "return"}:
            return "global"
        if re.match(r"^interface\s+", stripped, re.I):
            return "interface"
        if re.match(r"^router\s+(?:ospf|eigrp|bgp)\s+", stripped, re.I) or re.match(r"^ospf\s+\d+", stripped, re.I):
            return "routing"
        if re.match(r"^line\s+", stripped, re.I):
            return "line"
        if stripped.startswith("config "):
            return "config"
        if stripped.startswith("edit "):
            return "edit"
        if stripped.startswith("set ") and current == "global":
            return "set"
        return current

    @staticmethod
    def _validate_parameter_values(line: str, rule: CommandRule) -> str | None:
        if not rule.parameter_specs:
            return None
        tokens = line.split()
        for spec in rule.parameter_specs:
            if spec.name.startswith("__"):
                continue
            matches = [token for token in tokens if token not in line[:0]]
            if not matches:
                continue
            value = tokens[-1] if spec.variable_type not in {"keyword_set"} else tokens[-1]
            if spec.variable_type in VALIDATORS and not VALIDATORS[spec.variable_type](value):
                return f"invalid_{spec.variable_type}:{value}"
            if spec.choices and value not in spec.choices:
                return f"invalid_keyword:{value}"
            if spec.variable_type == "integer":
                try:
                    number = int(value)
                except ValueError:
                    return f"invalid_integer:{value}"
                if spec.minimum is not None and number < spec.minimum:
                    return f"integer_below_minimum:{value}"
                if spec.maximum is not None and number > spec.maximum:
                    return f"integer_above_maximum:{value}"
        return None

    def validate_line(self, line: str, line_number: int, vendor: str, platform: str, mode: str = "global") -> ValidationLineResult:
        """Validate one line and return its resulting mode."""
        stripped = line.strip()
        next_mode = self._mode_transition(stripped, mode)
        if not stripped or stripped.startswith("!") or stripped.startswith("#"):
            return ValidationLineResult(line_number, line, True, CoverageStatus.VALIDATED, (), next_mode)
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(stripped):
                diagnostic = ValidationDiagnostic("FORBIDDEN_COMMAND", "Command is forbidden in offline production validation.", Severity.ERROR, ValidationStage.SYNTAX, line_number, stripped, remediation="Remove the command or route it through an approved operational workflow.")
                return ValidationLineResult(line_number, line, False, CoverageStatus.VALIDATED, (diagnostic,), next_mode)
        rules = self.rules_for(vendor, platform)
        for rule in rules:
            if rule.matches(stripped):
                value_error = self._validate_parameter_values(stripped, rule)
                if value_error:
                    diagnostic = ValidationDiagnostic("INVALID_PARAMETER", value_error, Severity.ERROR, ValidationStage.SYNTAX, line_number, stripped, remediation="Correct the parameter according to the scoped grammar.")
                    return ValidationLineResult(line_number, line, False, rule.coverage_status, (diagnostic,), next_mode)
                return ValidationLineResult(line_number, line, True, rule.coverage_status, (), next_mode)
        if re.search(r"(?i)\b(?:invalid|not-a-real-command|this-is-not-valid)\b", stripped):
            diagnostic = ValidationDiagnostic("UNKNOWN_COMMAND", "Command is not present in the scoped grammar.", Severity.ERROR, ValidationStage.SYNTAX, line_number, stripped, remediation="Use a command covered by the vendor/version grammar or add authoritative evidence.")
            return ValidationLineResult(line_number, line, False, CoverageStatus.NOT_COVERED, (diagnostic,), next_mode)
        diagnostic = ValidationDiagnostic("SYNTAX_NOT_COVERED", "Command was not matched by the current offline grammar; no full syntax claim is made.", Severity.WARNING, ValidationStage.SYNTAX, line_number, stripped, coverage_status=CoverageStatus.NOT_COVERED, remediation="Add model/version-scoped grammar evidence before production deployment.")
        return ValidationLineResult(line_number, line, True, CoverageStatus.NOT_COVERED, (diagnostic,), next_mode)

    def validate(self, config_text: str, vendor: str, platform: str) -> list[ValidationLineResult]:
        """Validate every line offline."""
        mode = "global"
        results: list[ValidationLineResult] = []
        for number, line in enumerate(config_text.splitlines(), start=1):
            result = self.validate_line(line, number, vendor, platform, mode)
            results.append(result)
            mode = result.mode_after
        return results
