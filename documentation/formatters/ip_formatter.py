"""IP address formatting helpers."""
from __future__ import annotations

import ipaddress
from typing import Any


class IPFormatter:
    """Format IP networks without inventing allocations."""

    def format(self, value: Any) -> str:
        """Return canonical CIDR text when the value is valid, otherwise source text."""
        if value is None or value == "":
            return "PENDING: IP value not supplied"
        try:
            return str(ipaddress.ip_interface(str(value)))
        except ValueError:
            try:
                return str(ipaddress.ip_network(str(value), strict=False))
            except ValueError:
                return str(value)

    def summarize(self, networks: list[str]) -> list[str]:
        """Return canonical summaries for supplied networks only."""
        parsed = []
        for value in networks:
            try:
                parsed.append(ipaddress.ip_network(value, strict=False))
            except ValueError:
                continue
        return [str(item) for item in ipaddress.collapse_addresses(parsed)]
