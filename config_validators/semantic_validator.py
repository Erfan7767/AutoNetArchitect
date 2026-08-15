"""Offline semantic checks for common network configuration values."""
from __future__ import annotations

import ipaddress
import re

from .models import Severity, ValidationDiagnostic, ValidationStage
from .rules.common_rules import valid_asn, valid_dscp, valid_ipv4, valid_mask, valid_mtu, valid_priority, valid_stp_priority, valid_vlan


class SemanticValidator:
    """Check values and relationships that are independent of live device state."""

    def validate(self, config_text: str, vendor: str, platform: str) -> list[ValidationDiagnostic]:
        """Return semantic diagnostics."""
        diagnostics: list[ValidationDiagnostic] = []
        acl_sequences: set[tuple[str, str]] = set()
        route_map_sequences: set[tuple[str, str]] = set()
        for number, line in enumerate(config_text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("!", "#")):
                continue
            tokens = stripped.split()
            if len(tokens) >= 4 and tokens[0].lower() == "ip" and tokens[1].lower() == "address":
                address = tokens[2]
                mask = tokens[3]
                if not valid_ipv4(address):
                    diagnostics.append(self._diag("INVALID_INTERFACE_IP", "Interface IP address is not valid IPv4.", number, line))
                if valid_ipv4(address) and ipaddress.ip_address(address).is_unspecified:
                    diagnostics.append(self._diag("UNSPECIFIED_INTERFACE_IP", "Unspecified address cannot be used as an interface address.", number, line))
                if not valid_mask(mask):
                    diagnostics.append(self._diag("INVALID_NETMASK", "Dotted netmask is invalid or non-contiguous.", number, line))
            if tokens and tokens[0].lower() == "vlan" and len(tokens) >= 2 and not valid_vlan(tokens[1]):
                diagnostics.append(self._diag("INVALID_VLAN", "VLAN ID must be between 1 and 4094.", number, line))
            if len(tokens) >= 3 and tokens[0].lower() in {"router", "bgp"} and tokens[1].lower() == "bgp" and not valid_asn(tokens[2]):
                diagnostics.append(self._diag("INVALID_ASN", "BGP ASN must be in the four-byte range.", number, line))
            if tokens and tokens[0].lower() == "bgp" and len(tokens) >= 2 and not valid_asn(tokens[1]):
                diagnostics.append(self._diag("INVALID_ASN", "BGP ASN must be in the four-byte range.", number, line))
            if tokens and tokens[0].lower() == "spanning-tree" and "priority" in [token.lower() for token in tokens]:
                value = tokens[-1]
                if not valid_stp_priority(value):
                    diagnostics.append(self._diag("INVALID_STP_PRIORITY", "STP priority must be a multiple of 4096 within the platform range.", number, line))
            if tokens and tokens[0].lower() in {"standby", "vrrp"} and "priority" in [token.lower() for token in tokens]:
                value = tokens[-1]
                if not valid_priority(value):
                    diagnostics.append(self._diag("INVALID_FHRP_PRIORITY", "FHRP priority must be between 0 and 255.", number, line))
            if tokens and tokens[0].lower() in {"ip", "ipv6"} and "dscp" in [token.lower() for token in tokens]:
                value = tokens[-1]
                if not valid_dscp(value):
                    diagnostics.append(self._diag("INVALID_DSCP", "DSCP must be between 0 and 63.", number, line))
            if "mtu" in [token.lower() for token in tokens]:
                value = tokens[-1]
                if not valid_mtu(value):
                    diagnostics.append(self._diag("INVALID_MTU", "MTU is outside the supported offline range 576-9216.", number, line))
            if tokens and tokens[0].lower() == "route-map" and len(tokens) >= 4:
                key = (tokens[1], tokens[3])
                if key in route_map_sequences:
                    diagnostics.append(self._diag("DUPLICATE_ROUTE_MAP_SEQUENCE", "Route-map name and sequence are duplicated.", number, line))
                route_map_sequences.add(key)
            if tokens and tokens[0].lower() == "ip" and len(tokens) >= 6 and tokens[1].lower() == "access-list":
                key = (tokens[3], tokens[4])
                if key in acl_sequences:
                    diagnostics.append(self._diag("DUPLICATE_ACL_SEQUENCE", "ACL identifier and sequence are duplicated.", number, line))
                acl_sequences.add(key)
            if tokens and tokens[0].lower() == "interface" and not re.match(r"^[A-Za-z0-9][A-Za-z0-9./_-]+$", tokens[-1]):
                diagnostics.append(self._diag("INVALID_INTERFACE_NAME", "Interface name does not match the conservative platform-independent pattern.", number, line))
        return diagnostics

    @staticmethod
    def _diag(code: str, message: str, number: int, line: str) -> ValidationDiagnostic:
        return ValidationDiagnostic(code, message, Severity.ERROR, ValidationStage.SEMANTIC, number, line.strip(), remediation="Correct the value in the design artifact and regenerate configuration.")
