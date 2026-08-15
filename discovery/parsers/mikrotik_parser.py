"""Read-only parser for MikroTik RouterOS system output."""

from __future__ import annotations

from .parser_common import VendorParser


class MikroTikParser(VendorParser):
    """Parse RouterOS identity fields from explicitly captured output."""

    vendor = "mikrotik"
    parser_name = "mikrotik_parser"
    platform = "routeros"
    field_patterns = {
        "version": (r"^version:\s*([0-9A-Za-z._-]+)", r"RouterOS\s+([0-9A-Za-z._-]+)"),
        "model": (r"^board-name:\s*([^\r\n]+)", r"^platform:\s*([^\r\n]+)"),
        "serial": (r"^serial-number:\s*([A-Za-z0-9._-]+)",),
        "hostname": (r"^name:\s*([^\r\n]+)",),
    }
    observation_patterns = {
        "architecture": (r"^architecture-name:\s*([^\r\n]+)",),
        "uptime": (r"^uptime:\s*([^\r\n]+)",),
    }
