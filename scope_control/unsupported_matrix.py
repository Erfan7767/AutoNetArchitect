"""Unsupported capability matrix with explicit action paths."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class UnsupportedEntry:
    """One unsupported or conditionally supported capability."""
    category: str
    key: str
    status: str
    reason: str
    fallback: str
    human_action: str
class UnsupportedMatrix:
    """Classify unsupported vendors, protocols, HA, scale, sites, wireless, multicast, and regulatory contexts."""
    def __init__(self, entries: list[UnsupportedEntry] | None = None) -> None: self.entries = entries or self.default_entries()
    @staticmethod
    def default_entries() -> list[UnsupportedEntry]:
        """Return explicit conservative unsupported entries."""
        return [UnsupportedEntry("vendor", "unknown_vendor", "unsupported", "vendor is not in validated V1 library", "preview_only", "provide validated vendor evidence"), UnsupportedEntry("protocol", "mixed_unsupported_overlay", "unsupported", "protocol combination has no validated profile", "safe_refusal", "supply lab validation"), UnsupportedEntry("ha", "multi_active_unvalidated", "unsupported", "HA pattern is not validated", "preview_only", "obtain vendor design review"), UnsupportedEntry("scale", "over_500_devices", "unsupported", "scale exceeds validated boundary", "preview_only", "perform capacity and lab review"), UnsupportedEntry("site", "high_complexity_brownfield", "insufficient_evidence", "brownfield dependency graph is incomplete", "human_review", "complete inventory and dependencies"), UnsupportedEntry("wireless", "outdoor_mobility", "preview_only", "outdoor mobility requires specialist survey", "preview_only", "provide RF survey"), UnsupportedEntry("multicast", "inter_domain_multicast", "unsupported", "inter-domain behavior lacks validated evidence", "safe_refusal", "provide validated multicast design"), UnsupportedEntry("regulatory", "regulated_environment", "production_blocked", "regulatory approval is not inferable", "human_review", "obtain compliance approval")]
    def lookup(self, category: str, key: str) -> UnsupportedEntry | None:
        """Return matching matrix entry."""
        return next((entry for entry in self.entries if entry.category == category and entry.key == key), None)
