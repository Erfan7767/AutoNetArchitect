"""Read-only parser for Huawei VRP output."""

from __future__ import annotations

from .parser_common import VendorParser


class HuaweiParser(VendorParser):
    """Parse Huawei VRP identity fields from human-provided command output."""

    vendor = "huawei"
    parser_name = "huawei_parser"
    platform = "vrp"
    field_patterns = {
        "version": (r"Version\s+([0-9A-Za-z._-]+)", r"VRP.*?Version\s+([0-9A-Za-z._-]+)"),
        "model": (r"(?:MODEL|Model)\s*[: ]\s*([A-Za-z0-9._/-]+)", r"Product\s+name\s*:\s*([A-Za-z0-9._/-]+)"),
        "serial": (r"(?:ESN|Serial number)\s*[: ]\s*([A-Za-z0-9._/-]+)",),
        "hostname": (r"^sysname\s+([^\s]+)", r"^([A-Za-z0-9._-]+)<[^>]+>\s*$"),
    }
    observation_patterns = {
        "patch": (r"Patch version\s*[: ]\s*([0-9A-Za-z._-]+)",),
        "uptime": (r"uptime is\s+([^\r\n]+)",),
    }
