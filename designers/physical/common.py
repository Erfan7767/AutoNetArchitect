from designers.base_designer import BaseDesigner
class PhysicalInfrastructureDesigner(BaseDesigner):
    """Shared physical design helpers and explicit site assumptions."""
    def missing_site(self,r,keys):
        missing=[k for k in keys if not r.get(k)]
        for k in missing:self.record_assumption(k,None,"HumanSuppliedMandatory: exact site measurement is not supplied")
        return missing
