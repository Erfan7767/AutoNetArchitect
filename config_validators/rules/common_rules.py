"""Shared parameter validators and command rule contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
import ipaddress
import re
from typing import Any, Callable

from config_validators.models import CoverageStatus


@dataclass(frozen=True)
class ParameterSpec:
    """One command parameter specification."""

    name: str
    variable_type: str
    required: bool = True
    choices: tuple[str, ...] = ()
    minimum: int | None = None
    maximum: int | None = None


@dataclass(frozen=True)
class CommandRule:
    """Regex-backed command rule with coverage and valid modes."""

    command_pattern: str
    parameter_specs: tuple[ParameterSpec, ...] = ()
    valid_modes: tuple[str, ...] = ("global",)
    deprecated: bool = False
    min_version: str | None = None
    coverage_status: CoverageStatus = CoverageStatus.VALIDATED
    description: str = ""
    _compiled: re.Pattern[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_compiled", re.compile(self.command_pattern))

    def matches(self, line: str) -> bool:
        """Return whether the rule matches a command line."""
        return bool(self._compiled.fullmatch(line.strip()))


def valid_ipv4(value: str) -> bool:
    """Validate an IPv4 address."""
    try:
        return ipaddress.ip_address(value).version == 4
    except ValueError:
        return False


def valid_ipv6(value: str) -> bool:
    """Validate an IPv6 address."""
    try:
        return ipaddress.ip_address(value).version == 6
    except ValueError:
        return False


def valid_network(value: str) -> bool:
    """Validate CIDR network notation."""
    try:
        ipaddress.ip_network(value, strict=False)
        return "/" in value
    except ValueError:
        return False


def valid_mask(value: str) -> bool:
    """Validate dotted IPv4 netmask."""
    try:
        ipaddress.IPv4Network(f"0.0.0.0/{value}")
        return "." in value
    except ValueError:
        return False


def valid_vlan(value: str) -> bool:
    """Validate a VLAN ID."""
    try:
        return 1 <= int(value) <= 4094
    except ValueError:
        return False


def valid_asn(value: str) -> bool:
    """Validate a four-byte ASN range."""
    try:
        return 1 <= int(value) <= 4294967295
    except ValueError:
        return False


def valid_dscp(value: str) -> bool:
    """Validate DSCP range."""
    try:
        return 0 <= int(value) <= 63
    except ValueError:
        return False


def valid_stp_priority(value: str) -> bool:
    """Validate STP priority multiples."""
    try:
        return 0 <= int(value) <= 61440 and int(value) % 4096 == 0
    except ValueError:
        return False


def valid_priority(value: str) -> bool:
    """Validate FHRP priority range."""
    try:
        return 0 <= int(value) <= 255
    except ValueError:
        return False


def valid_mtu(value: str) -> bool:
    """Validate conservative Ethernet MTU range."""
    try:
        return 576 <= int(value) <= 9216
    except ValueError:
        return False


def valid_hostname(value: str) -> bool:
    """Validate a DNS-compatible hostname label."""
    return bool(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,62}[A-Za-z0-9])?", value))


VALIDATORS: dict[str, Callable[[str], bool]] = {
    "ip": valid_ipv4,
    "ipv4": valid_ipv4,
    "ipv6": valid_ipv6,
    "network": valid_network,
    "cidr": valid_network,
    "mask": valid_mask,
    "vlan": valid_vlan,
    "asn": valid_asn,
    "dscp": valid_dscp,
    "stp_priority": valid_stp_priority,
    "priority": valid_priority,
    "mtu": valid_mtu,
    "hostname": valid_hostname,
}

FORBIDDEN_PATTERNS = (
    re.compile(r"(?i)^\s*(?:debug|reload|write\s+erase|erase\s+startup-config)\b"),
    re.compile(r"(?i)\b(?:password|passwd|psk|private-key)\s+(?![589]\s+secret://|secret://)[^\s]+"),
)
