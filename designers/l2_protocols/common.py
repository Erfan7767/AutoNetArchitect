"""Shared Layer-2 helpers."""
from designers.base_designer import BaseDesigner
class L2Designer(BaseDesigner):
    """Base L2 designer with platform evidence gating."""
    def supported(self, requirements:dict)->bool:
        """Return whether platform support is explicitly evidenced."""
        return bool(requirements.get("platform_support_evidence_ids"))
    def evidence_status(self, requirements:dict)->str:
        """Expose capability evidence state."""
        return "evidence_backed" if self.supported(requirements) else "evidence_required"
