"""Detection and production blocking of stale knowledge."""
from __future__ import annotations
from datetime import date
class StaleClaimDetector:
    """Detect stale, blocked, or insufficient lifecycle items."""
    def detect(self, items: list[object], today: date | None = None) -> list[object]:
        """Return items whose freshness expiry has passed or state is invalid."""
        current = today or date.today(); stale = []
        for item in items:
            expiry = getattr(item, "freshness_expiry", None)
            if getattr(item, "freshness_state", "") == "stale" or (expiry is not None and expiry < current):
                item.freshness_state = "stale"; item.publication_state = "blocked"; stale.append(item)
        return stale
    def production_allowed(self, item: object) -> bool:
        """Return whether a consumer may use the item in production."""
        return getattr(item, "publication_state", "") == "published" and getattr(item, "freshness_state", "") == "fresh"
