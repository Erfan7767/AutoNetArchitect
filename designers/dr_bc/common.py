from designers.base_designer import BaseDesigner
class DRDesigner(BaseDesigner):
    """Shared DR network contracts and mandatory field handling."""
    def mandatory(self,r,keys):
        missing=[k for k in keys if not r.get(k)]
        for k in missing:self.record_assumption(k,None,"HumanSuppliedMandatory: DR site or replication detail is not inferable")
        return missing
