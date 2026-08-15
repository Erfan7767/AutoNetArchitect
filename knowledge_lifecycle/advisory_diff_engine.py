"""Diff advisories and mark impacted claims."""
from __future__ import annotations
class AdvisoryDiffEngine:
    """Compare advisory claim sets."""
    def diff(self, before: dict[str, object], after: dict[str, object]) -> dict[str, list[str]]:
        """Return added, changed, and removed claim keys."""
        before_keys, after_keys = set(before), set(after); changed = [key for key in before_keys & after_keys if before[key] != after[key]]; return {"added": sorted(after_keys - before_keys), "removed": sorted(before_keys - after_keys), "changed": sorted(changed)}
