"""Read-only parser for Juniper Junos operational output."""

from __future__ import annotations

from .parser_common import VendorParser


class JuniperParser(VendorParser):
    """Parse Junos identity fields from supplied command output."""

    vendor = "juniper"
    parser_name = "juniper_parser"
    platform = "junos"
    field_patterns = {
        "version": (r"Junos:\s*([0-9A-Za-z._-]+)", r"JUNOS Base OS boot\s*\[([^\]]+)\]"),
        "model": (r"Model:\s*([A-Za-z0-9._/-]+)", r"Chassis\s+(?!serial\b)([A-Za-z0-9._/-]+)"),
        "serial": (r"Chassis serial number:\s*([A-Za-z0-9._/-]+)", r"Serial number:\s*([A-Za-z0-9._/-]+)"),
        "hostname": (r"Model:\s*[^\r\n]+\n(?:.*\n){0,8}?System booted", r"^set system host-name\s+([^\s]+)"),
    }
    observation_patterns = {
        "booted": (r"System booted:\s*([^\r\n]+)",),
        "kernel": (r"JUNOS Kernel Software suite\s*\[([^\]]+)\]",),
    }
