"""Read-only parser for Cisco IOS XE, IOS, NX-OS, ASA, and WLC outputs."""

from __future__ import annotations

from .parser_common import VendorParser


class CiscoParser(VendorParser):
    """Parse Cisco official-platform identity fields from supplied output."""

    vendor = "cisco"
    parser_name = "cisco_parser"
    platform = "cisco"
    field_patterns = {
        "version": (r"(?:Version|version)\s+([0-9A-Za-z._()/-]+)", r"NXOS:\s+version\s+([0-9A-Za-z._()/-]+)"),
        "model": (r"(?:Model number|Chassis type|Product ID)\s*[: ]\s*([A-Za-z0-9._/-]+)", r"cisco\s+(?:ASR|ISR|C|N|WS|AIR|ASA)([A-Za-z0-9._/-]+)"),
        "serial": (r"(?:Processor board ID|System serial number|Serial number)\s*[: ]\s*([A-Za-z0-9._/-]+)", r"License UDI:\s+PID:([A-Za-z0-9._/-]+),VID:[^,]+,SN:([A-Za-z0-9._/-]+)"),
        "hostname": (r"^hostname\s+([^\s#]+)", r"^([A-Za-z0-9._-]+)[>#]\s*$"),
    }
    observation_patterns = {
        "config_register": (r"Configuration register is\s+([0-9A-Fa-fx]+)",),
        "uptime": (r"uptime is\s+([^\r\n]+)",),
    }
