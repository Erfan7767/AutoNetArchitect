"""Detect changes in vendor knowledge feeds."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class VendorChange:
    """Detected vendor content change."""
    source_id: str
    previous_hash: str
    current_hash: str
    change_type: str
class VendorChangeMonitor:
    """Compare feed hashes and classify changes."""
    def compare(self, source_id: str, previous_hash: str, current_hash: str) -> VendorChange | None:
        """Return a change record when hashes differ."""
        return None if previous_hash == current_hash else VendorChange(source_id, previous_hash, current_hash, "content_changed")
