"""Shared NAT helpers and mandatory field handling."""
from designers.base_designer import BaseDesigner
class NATDesigner(BaseDesigner):
    """Common NAT designer that never fabricates public addressing."""
    def required_public_data(self,r,keys):
        """Record missing public data as human-supplied mandatory."""
        missing=[k for k in keys if not r.get(k)]
        for key in missing:self.record_assumption(key,None,"HumanSuppliedMandatory: public NAT data is not inferable")
        return missing
    def evidence_status(self,r):
        """Return platform evidence state."""
        return "evidence_backed" if r.get("platform_support_evidence_ids") else "evidence_required"
