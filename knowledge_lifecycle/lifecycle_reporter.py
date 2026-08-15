"""Knowledge lifecycle reporting."""
from __future__ import annotations
class LifecycleReporter:
    """Summarize knowledge changes and production blocks."""
    def report(self, items: list[object], changes: list[object] | None = None) -> dict[str, list[object]]:
        """Return newly added, changed, deprecated, and blocked knowledge."""
        return {"newly_added": [item for item in items if getattr(item, "status", "") == "ingested"], "changed": list(changes or []), "deprecated": [item for item in items if getattr(item, "publication_state", "") == "deprecated"], "blocked_claims": [item for item in items if getattr(item, "publication_state", "") == "blocked"]}
