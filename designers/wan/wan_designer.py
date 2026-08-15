"""WAN handoff designer."""
from designers.base_designer import BaseDesigner
class WANDesigner(BaseDesigner):
    """Design WAN intent and block missing ISP handoff data."""
    def design(self,requirements):
        handoff=requirements.get("isp_handoff")
        if not handoff:
            self.record_assumption("isp_handoff",None,"mandatory human-supplied ISP handoff data is missing")
            return {"status":"blocked_pending_human_mandatory","human_supplied_mandatory":["isp_handoff"],"decisions":self.decisions,"assumptions":self.assumptions}
        self.record_decision("wan_handoff",handoff,"uses supplied ISP handoff parameters")
        return {"status":"designed","isp_handoff":handoff,"decisions":self.decisions,"assumptions":self.assumptions}
