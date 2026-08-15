"""Shared FHRP designer helpers."""
from designers.base_designer import BaseDesigner
class FHRPDesigner(BaseDesigner):
    """Common designer with capability evidence gating."""
    def evidence_status(self,r):
        """Return evidence status for platform features."""
        return "evidence_backed" if r.get("platform_support_evidence_ids") else "evidence_required"
