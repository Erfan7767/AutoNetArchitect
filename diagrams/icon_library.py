"""Vendor-aware icon selection with explicit generic fallback."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class IconLibrary:
    """Resolve icon references from vendor and node type mappings."""

    def __init__(self, mapping_path: str | Path | None = None) -> None:
        """Load mapping data or use the bounded built-in fallback."""
        self.mapping_path = Path(mapping_path) if mapping_path else Path(__file__).parent / "data" / "icon_mappings.json"
        self.mappings: dict[str, Any] = self._load()

    def select(self, *, vendor: str | None, node_type: str) -> str:
        """Return a vendor-specific icon when mapped, otherwise a generic reference."""
        vendor_key = (vendor or "generic").strip().lower().replace(" ", "")
        type_key = node_type.strip().lower()
        lookup_keys = ["switch", "switch_l2"] if type_key == "switch_l2" else [type_key]
        vendor_map = self.mappings.get("vendors", {}).get(vendor_key, {})
        generic_map = self.mappings.get("generic", {})
        for lookup_key in lookup_keys:
            if vendor_map.get(lookup_key):
                return str(vendor_map[lookup_key])
            if generic_map.get(lookup_key):
                return str(generic_map[lookup_key])
        return str(generic_map.get("unknown", "generic/unknown"))

    def available_vendors(self) -> list[str]:
        """Return mapped vendor families."""
        return sorted(str(item) for item in self.mappings.get("vendors", {}).keys())

    def _load(self) -> dict[str, Any]:
        """Load valid JSON mapping or return deterministic fallback mappings."""
        fallback = {"generic": {"unknown": "generic/unknown", "router": "generic/router", "switch_l2": "generic/switch", "switch_l3": "generic/switch_l3", "firewall": "generic/firewall", "access_point": "generic/access_point", "server": "generic/server", "cloud": "generic/cloud", "internet": "generic/internet", "site": "generic/site", "building": "generic/building", "rack": "generic/rack"}, "vendors": {}}
        if not self.mapping_path.exists():
            return fallback
        try:
            value = json.loads(self.mapping_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return fallback
        return value if isinstance(value, dict) else fallback
