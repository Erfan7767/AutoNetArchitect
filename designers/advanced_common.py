"""Shared advanced designer contracts."""
from designers.base_designer import BaseDesigner
class AdvancedDesigner(BaseDesigner):
    """Enforce source-of-truth and mandatory input semantics."""
    def mandatory(self,r,keys):
        missing=[k for k in keys if not r.get(k)]
        for k in missing:self.record_assumption(k,None,"HumanSuppliedMandatory: value is not inferable")
        return missing
    def source(self,r):
        """Expose the authoritative source used by the design."""
        return r.get("source_of_truth","requirements_document")
