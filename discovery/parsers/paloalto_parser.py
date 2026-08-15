"""Read-only parser for Palo Alto PAN-OS operational output."""

from __future__ import annotations

from .parser_common import VendorParser


class PaloAltoParser(VendorParser):
    """Parse PAN-OS system identity fields without capability assumptions."""

    vendor = "paloalto"
    parser_name = "paloalto_parser"
    platform = "panos"
    field_patterns = {
        "version": (r"(?:sw-version|app-version)\s*:\s*([0-9A-Za-z._-]+)", r"PAN-OS\s+([0-9A-Za-z._-]+)"),
        "model": (r"model\s*:\s*([A-Za-z0-9._/-]+)", r"family\s*:\s*([A-Za-z0-9._/-]+)"),
        "serial": (r"serial\s*:\s*([A-Za-z0-9._/-]+)", r"serial-number\s*:\s*([A-Za-z0-9._/-]+)"),
        "hostname": (r"hostname\s*:\s*([^\r\n]+)", r"set deviceconfig system hostname\s+([^\s]+)"),
    }
    observation_patterns = {
        "multi_vsys": (r"multi-vsys\s*:\s*(yes|no|enabled|disabled)",),
        "ha_state": (r"(?:ha state|state)\s*:\s*(active|passive|unknown)",),
    }
