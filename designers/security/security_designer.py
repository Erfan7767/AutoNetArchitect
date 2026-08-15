"""Intent-based security designer."""
from designers.base_designer import BaseDesigner
class SecurityDesigner(BaseDesigner):
    """Translate security intent into zones, groups, and owned rules."""
    def design(self,requirements):
        zones=requirements.get("zones",["inside","outside","dmz"]);objects=requirements.get("object_groups",{});services=requirements.get("service_groups",{});rules=[]
        for intent in requirements.get("intents",[]):rules.append({"source":intent.get("source"),"destination":intent.get("destination"),"service":intent.get("service"),"action":intent.get("action","deny"),"owner":intent.get("owner","security")})
        self.record_decision("security_policy",zones,"intent translated to explicit zones and owned rules")
        return {"zones":zones,"object_groups":objects,"service_groups":services,"rules":rules,"decisions":self.decisions,"assumptions":self.assumptions}
