"""Read-only parser for Aruba AOS-CX operational output."""

from __future__ import annotations

from .parser_common import VendorParser


class ArubaParser(VendorParser):
    """Parse Aruba AOS-CX identity and selected operational observations."""

    vendor = "aruba"
    parser_name = "aruba_parser"
    platform = "aoscx"
    field_patterns = {
        "version": (r"ArubaOS-CX\s+([0-9A-Za-z._-]+)", r"Software Version\s*:\s*([0-9A-Za-z._-]+)"),
        "model": (r"Product Name\s*:\s*([A-Za-z0-9._/-]+)", r"Chassis\s*:\s*([A-Za-z0-9._/-]+)"),
        "serial": (r"Serial Number\s*:\s*([A-Za-z0-9._/-]+)", r"Serial\s*:\s*([A-Za-z0-9._/-]+)"),
        "hostname": (r"Hostname\s*:\s*([^\r\n]+)", r"^hostname\s+(?!:)([^\s]+)"),
    }
    observation_patterns = {
        "boot_time": (r"Boot Time\s*:\s*([^\r\n]+)",),
        "switch_role": (r"Switch Role\s*:\s*([^\r\n]+)",),
    }
