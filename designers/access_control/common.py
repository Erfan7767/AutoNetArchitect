"""Shared NAC helpers."""
from designers.base_designer import BaseDesigner
class NACDesigner(BaseDesigner):
    """Base NAC designer with mandatory infrastructure handling."""
    def mandatory(self,r,keys):
        missing=[k for k in keys if not r.get(k)]
        for k in missing:self.record_assumption(k,None,"HumanSuppliedMandatory: NAC infrastructure detail is not inferable")
        return missing
    def evidence(self,r):
        """Return platform capability evidence state."""
        return "evidence_backed" if r.get("capability_evidence_ids") else "evidence_required"
