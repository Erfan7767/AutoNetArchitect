"""Offline cross-reference validation for named configuration objects."""
from __future__ import annotations

import re
from typing import Any

from .models import Severity, ValidationDiagnostic, ValidationStage


class CrossReferenceValidator:
    """Validate references against definitions in the same configuration and supplied inventory."""

    def validate(self, config_text: str, vendor: str, platform: str, context: dict[str, Any] | None = None) -> list[ValidationDiagnostic]:
        """Return diagnostics for unresolved internal references."""
        context = context or {}
        lines = config_text.splitlines()
        defined: dict[str, set[str]] = {key: set() for key in ("acl", "route_map", "prefix_list", "vrf", "vlan", "track", "class_map", "policy_map", "nat_pool", "interface", "port_channel", "key_chain")}
        for line in lines:
            stripped = line.strip()
            tokens = stripped.split()
            if not tokens:
                continue
            if tokens[0].lower() == "interface" and len(tokens) > 1:
                defined["interface"].add(tokens[1])
                if tokens[1].lower().startswith("port-channel"):
                    defined["port_channel"].add(tokens[1])
                if tokens[1].lower().startswith("vlan") and tokens[1][4:].isdigit():
                    defined["vlan"].add(tokens[1][4:])
            if tokens[0].lower() == "vlan" and len(tokens) > 1:
                defined["vlan"].add(tokens[1])
            if tokens[0].lower() == "route-map" and len(tokens) > 1:
                defined["route_map"].add(tokens[1])
            if tokens[:3] == ["ip", "prefix-list", tokens[2]] if len(tokens) > 2 else False:
                defined["prefix_list"].add(tokens[2])
            if tokens[:2] == ["ip", "access-list"] and len(tokens) > 2:
                defined["acl"].add(tokens[3] if tokens[2].lower() in {"standard", "extended"} and len(tokens) > 3 else tokens[2])
            if tokens[0].lower() in {"class-map", "class_map"} and len(tokens) > 1:
                defined["class_map"].add(tokens[-1])
            if tokens[0].lower() in {"policy-map", "policy_map"} and len(tokens) > 1:
                defined["policy_map"].add(tokens[-1])
            if tokens[0].lower() in {"vrf", "vrf-definition"} and len(tokens) > 2:
                defined["vrf"].add(tokens[-1])
            if tokens[0].lower() == "track" and len(tokens) > 1:
                defined["track"].add(tokens[1])
            if tokens[0].lower() == "key" and len(tokens) > 2 and tokens[1].lower() == "chain":
                defined["key_chain"].add(tokens[2])
        for key, values in context.get("definitions", {}).items():
            if key in defined and isinstance(values, list):
                defined[key].update(str(value) for value in values)
        diagnostics: list[ValidationDiagnostic] = []
        interface_inventory = {str(value) for value in context.get("interface_inventory", [])}
        for number, line in enumerate(lines, 1):
            stripped = line.strip()
            tokens = stripped.split()
            if not tokens:
                continue
            refs: list[tuple[str, str, str]] = []
            if tokens[0].lower() in {"route-map", "service-policy", "ip", "access-group", "ipsec"}:
                if len(tokens) > 3 and tokens[0].lower() == "ip" and tokens[1].lower() in {"vrf", "vrf-forwarding"} and tokens[2].lower() in {"forwarding", "member"}:
                    refs.append(("vrf", tokens[3], "ip vrf forwarding"))
                for index, token in enumerate(tokens):
                    lower = token.lower()
                    if lower == "route-map" and index + 1 < len(tokens):
                        refs.append(("route_map", tokens[index + 1], "route-map"))
                    if lower == "prefix-list" and index + 1 < len(tokens):
                        refs.append(("prefix_list", tokens[index + 1], "prefix-list"))
                    if lower in {"access-group", "access-class"} and index + 1 < len(tokens):
                        refs.append(("acl", tokens[index + 1], lower))
                    if lower in {"service-policy", "policy-map"} and index + 1 < len(tokens):
                        refs.append(("policy_map", tokens[index + 1], lower))
                    if lower == "track" and index + 1 < len(tokens):
                        refs.append(("track", tokens[index + 1], lower))
                    if lower in {"vrf", "vrf-forwarding", "vrf-member"} and index + 1 < len(tokens) and not (index + 1 < len(tokens) and tokens[index + 1].lower() in {"forwarding", "member"}):
                        refs.append(("vrf", tokens[index + 1], lower))
            if tokens[0].lower() == "channel-group" and len(tokens) > 1:
                refs.append(("port_channel", f"Port-channel{tokens[1]}", "channel-group"))
            if tokens[0].lower() == "interface" and len(tokens) > 1 and interface_inventory and tokens[1] not in interface_inventory:
                refs.append(("interface", tokens[1], "interface inventory"))
            for kind, name, source in refs:
                if name not in defined.get(kind, set()):
                    diagnostics.append(ValidationDiagnostic("UNRESOLVED_REFERENCE", f"{kind} reference {name!r} is not defined.", Severity.ERROR, ValidationStage.CROSS_REFERENCE, number, stripped, name, source, f"Define {kind} {name} before using it.", metadata={"reference_kind": kind}))
        return diagnostics
