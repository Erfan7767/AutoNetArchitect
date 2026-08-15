from designers.access_control.common import NACDesigner
class SGTDesigner(NACDesigner):
 def design(self,r):
  enabled=bool(r.get("sgt_enabled"));self.record_decision("sgt",enabled,"Cisco TrustSec is optional and vendor-specific")
  return {"status":"evidence_required" if enabled and not self.evidence(r)=="evidence_backed" else "designed","enabled":enabled,"assignments":r.get("assignments",{}),"sgacl_matrix":r.get("sgacl_matrix",{}),"propagation":r.get("propagation","SXP"),"decisions":self.decisions}
