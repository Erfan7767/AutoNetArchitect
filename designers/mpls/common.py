from designers.base_designer import BaseDesigner
class MPLSDesigner(BaseDesigner):
    """Shared MPLS contracts and SP mandatory data handling."""
    def mandatory(self,r,keys):
        missing=[k for k in keys if not r.get(k)]
        for k in missing:self.record_assumption(k,None,"HumanSuppliedMandatory: SP contract or PE detail is not inferable")
        return missing
