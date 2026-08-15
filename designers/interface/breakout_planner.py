from designers.interface.common import InterfaceDesigner
class BreakoutPlanner(InterfaceDesigner):
    """Plan supported breakout ratios without asserting platform support."""
    OPTIONS={"40G":["4x10G"],"100G":["4x25G","2x50G"],"400G":["4x100G","8x50G"]}
    def design(self,r):
        speed=r.get("speed");option=r.get("option");valid=option in self.OPTIONS.get(speed,[]);self.record_decision("breakout",{"speed":speed,"option":option},"breakout requires model-level support evidence");return {"valid_pattern":valid,"status":"evidence_required" if valid and not r.get("platform_support_evidence_ids") else "planned" if valid else "unsupported_pattern","decisions":self.decisions}
