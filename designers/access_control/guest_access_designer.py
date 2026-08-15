from designers.access_control.common import NACDesigner
class GuestAccessDesigner(NACDesigner):
 def design(self,r):
  missing=self.mandatory(r,["portal_server"]);self.record_decision("guest_access",True,"guest access is isolated and time/bandwidth constrained")
  return {"status":"blocked_missing_human_data" if missing else "designed","guest_vlan":r.get("guest_vlan"),"portal_server":r.get("portal_server"),"workflow":r.get("workflow","self_registration"),"restrictions":["internet_only","time_limited"],"decisions":self.decisions,"assumptions":self.assumptions}
