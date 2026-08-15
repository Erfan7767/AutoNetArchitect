"""Shared interface assignment helpers."""
from designers.base_designer import BaseDesigner
class InterfaceDesigner(BaseDesigner):
    """Base interface designer with equipment evidence gates."""
    def model_status(self,r):
        """Return model-map status without fabricating ports."""
        return "evidence_backed" if r.get("platform_port_map") else "HumanSuppliedMandatory"
    def require_model(self,r):
        """Record missing equipment model evidence."""
        if not r.get("equipment_model"): self.record_assumption("equipment_model",None,"HumanSuppliedMandatory: slot/module/port numbering cannot be inferred")
        if not r.get("platform_port_map"): self.record_assumption("platform_port_map",None,"HumanSuppliedMandatory: exact port inventory is unavailable")
