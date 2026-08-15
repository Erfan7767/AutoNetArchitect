"""Offline vendor-aware configuration structure validation."""
from __future__ import annotations

import re

from .models import Severity, ValidationBlockResult, ValidationDiagnostic, ValidationStage


class StructuralValidator:
    """Validate hierarchy and mode structure without contacting a device."""

    def validate(self, config_text: str, vendor: str, platform: str) -> ValidationBlockResult:
        """Return structural diagnostics for a complete configuration."""
        key = f"{vendor}_{platform}".lower().replace(" ", "_").replace("-", "_")
        if "fortinet" in key or "fortios" in key:
            return self._fortigate(config_text)
        if "palo" in key or "panos" in key or "pan_os" in key:
            return self._paloalto(config_text)
        if "juniper" in key or "junos" in key:
            return self._junos(config_text)
        if "mikrotik" in key or "routeros" in key:
            return self._mikrotik(config_text)
        return self._cisco_like(config_text, "huawei" in key)

    @staticmethod
    def _diagnostic(code: str, message: str, line_number: int, line: str, severity: Severity = Severity.ERROR) -> ValidationDiagnostic:
        return ValidationDiagnostic(code, message, severity, ValidationStage.STRUCTURAL, line_number, line.strip(), remediation="Correct the mode hierarchy and revalidate offline.")

    def _cisco_like(self, text: str, huawei: bool) -> ValidationBlockResult:
        diagnostics: list[ValidationDiagnostic] = []
        stack: list[str] = []
        parent_commands = re.compile(r"^(?:interface\s+.+|router\s+(?:ospf|eigrp|bgp)\s+.+|ospf\s+\d+.*|line\s+.+|vlan\s+\d+|ip\s+access-list\s+.+|route-map\s+.+|class-map\s+.+|policy-map\s+.+|crypto\s+ikev2\s+.+|aaa\s+new-model)$", re.I)
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("!") or stripped.startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())
            if stripped.lower() in {"exit", "quit", "return"}:
                if not stack:
                    diagnostics.append(self._diagnostic("ORPHAN_EXIT", "Mode exit has no open parent mode.", number, line))
                else:
                    stack.pop()
                continue
            if stripped.lower() == "end":
                stack.clear()
                continue
            if parent_commands.match(stripped):
                if indent != 0:
                    diagnostics.append(self._diagnostic("PARENT_INDENTED", "A mode-opening command must be at global indentation.", number, line))
                stack.append(stripped.split()[0].lower())
                continue
            if indent > 0 and not stack:
                diagnostics.append(self._diagnostic("ORPHAN_SUBCOMMAND", "Indented sub-command has no open parent mode.", number, line))
            if indent == 0 and stack:
                diagnostics.append(self._diagnostic("UNCLOSED_MODE", "A new global command appears before the parent mode was closed.", number, line))
                stack.clear()
        if stack:
            diagnostics.append(self._diagnostic("DANGLING_MODE", "Configuration ends with an open mode block.", len(text.splitlines()) or 1, ""))
        return ValidationBlockResult(not diagnostics, "huawei_cli" if huawei else "cisco_like_cli", tuple(diagnostics))

    def _fortigate(self, text: str) -> ValidationBlockResult:
        diagnostics: list[ValidationDiagnostic] = []
        config_depth = 0
        edit_depth = 0
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("config "):
                config_depth += 1
            elif stripped.startswith("edit "):
                if config_depth <= 0:
                    diagnostics.append(self._diagnostic("EDIT_OUTSIDE_CONFIG", "FortiOS edit must be nested inside config.", number, line))
                edit_depth += 1
            elif stripped == "next":
                if edit_depth <= 0:
                    diagnostics.append(self._diagnostic("ORPHAN_NEXT", "FortiOS next has no open edit block.", number, line))
                else:
                    edit_depth -= 1
            elif stripped == "end":
                if edit_depth:
                    diagnostics.append(self._diagnostic("EDIT_NOT_CLOSED", "FortiOS config block closes with an open edit block.", number, line))
                    edit_depth = 0
                elif config_depth <= 0:
                    diagnostics.append(self._diagnostic("ORPHAN_END", "FortiOS end has no open config block.", number, line))
                else:
                    config_depth -= 1
            elif stripped.startswith(("set ", "unset ", "append ")) and config_depth <= 0:
                diagnostics.append(self._diagnostic("SET_OUTSIDE_CONFIG", "FortiOS setting must be nested inside a config block.", number, line))
        if edit_depth or config_depth:
            diagnostics.append(self._diagnostic("DANGLING_FORTIOS_BLOCK", "FortiOS configuration ends with an open config/edit block.", len(text.splitlines()) or 1, ""))
        return ValidationBlockResult(not diagnostics, "fortigate_cli", tuple(diagnostics))

    def _paloalto(self, text: str) -> ValidationBlockResult:
        diagnostics: list[ValidationDiagnostic] = []
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not re.match(r"^(?:set|delete|edit|move|clone|rename|configure|commit|exit|quit|show)(?:\s|$)", stripped):
                diagnostics.append(self._diagnostic("PANOS_INVALID_ROOT", "PAN-OS line does not begin with a recognized CLI action.", number, line))
        return ValidationBlockResult(not diagnostics, "panos_set_cli", tuple(diagnostics))

    def _junos(self, text: str) -> ValidationBlockResult:
        diagnostics: list[ValidationDiagnostic] = []
        balance = 0
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            balance += stripped.count("{") - stripped.count("}")
            if balance < 0:
                diagnostics.append(self._diagnostic("JUNOS_UNBALANCED_BRACE", "Junos closing brace has no matching opening brace.", number, line))
            if not re.match(r"^(?:set|delete|deactivate|activate|rename|insert|configure|commit|exit|rollback|show|[{};])(?:\s|$)", stripped):
                diagnostics.append(self._diagnostic("JUNOS_INVALID_ROOT", "Junos line is not a recognized set command or hierarchy token.", number, line))
        if balance:
            diagnostics.append(self._diagnostic("JUNOS_DANGLING_BRACE", "Junos hierarchy has unclosed braces.", len(text.splitlines()) or 1, ""))
        return ValidationBlockResult(not diagnostics, "junos_cli", tuple(diagnostics))

    def _mikrotik(self, text: str) -> ValidationBlockResult:
        diagnostics: list[ValidationDiagnostic] = []
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not stripped.startswith("/"):
                diagnostics.append(self._diagnostic("ROUTEROS_PATH_REQUIRED", "RouterOS commands must start with a slash path.", number, line))
        return ValidationBlockResult(not diagnostics, "routeros_path_cli", tuple(diagnostics))
