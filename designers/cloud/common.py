from designers.base_designer import BaseDesigner
class CloudDesigner(BaseDesigner):
    """Shared cloud connectivity contracts and mandatory fields."""
    def mandatory(self,r,keys):
        missing=[k for k in keys if not r.get(k)]
        for k in missing:self.record_assumption(k,None,"HumanSuppliedMandatory: cloud provider detail is not inferable")
        return missing
    def source(self,r):
        return r.get("source_of_truth","requirements_document")
