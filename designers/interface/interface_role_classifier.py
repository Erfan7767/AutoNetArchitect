from designers.interface.common import InterfaceDesigner
class InterfaceRoleClassifier(InterfaceDesigner):
    """Classify interfaces from topology intent and device role."""
    def design(self,r):
        assignments=[{"interface":x.get("interface"),"role":x.get("role","unused"),"rationale":"topology role supplied"} for x in r.get("connections",[])];self.record_decision("interface_roles",assignments,"roles derive from topology and endpoint intent");return {"assignments":assignments,"decisions":self.decisions}
