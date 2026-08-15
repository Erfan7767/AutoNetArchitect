"""Read-only parser for Fortinet FortiOS diagnostic output."""

from __future__ import annotations

from .parser_common import VendorParser


class FortinetParser(VendorParser):
    """Parse FortiOS identity fields from an explicitly supplied snapshot."""

    vendor = "fortinet"
    parser_name = "fortinet_parser"
    platform = "fortios"
    field_patterns = {
        "version": (r"Version:\s*v?([0-9A-Za-z._-]+)", r"FortiOS\s+v?([0-9A-Za-z._-]+)"),
        "model": (r"Model name:\s*([^\r\n,]+)", r"Version:.*?\((FortiGate-[^)]+)\)"),
        "serial": (r"Serial-Number:\s*([A-Za-z0-9._-]+)", r"Serial number:\s*([A-Za-z0-9._-]+)"),
        "hostname": (r"Hostname:\s*([^\r\n]+)", r"set hostname\s+([^\s]+)"),
    }
    observation_patterns = {
        "operation_mode": (r"Operation mode:\s*([^\r\n]+)",),
        "virtual_domains": (r"Virtual domains:\s*([0-9]+)",),
    }
