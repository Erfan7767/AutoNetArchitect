from designers.base_designer import BaseDesigner
class VoiceDesigner(BaseDesigner):
    """Shared voice network contracts and mandatory platform handling."""
    def mandatory(self,r,keys):
        missing=[k for k in keys if not r.get(k)]
        for k in missing:self.record_assumption(k,None,"HumanSuppliedMandatory: Voice/UC platform or service detail is not inferable")
        return missing
