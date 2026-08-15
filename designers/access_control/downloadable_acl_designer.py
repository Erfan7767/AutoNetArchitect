from designers.access_control.common import NACDesigner
class DownloadableACLDesigner(NACDesigner):
 def design(self,r):
  roles=r.get("roles",["employee","contractor","guest","quarantine"]);self.record_decision("downloadable_acl",roles,"role-specific dACL with platform and performance review")
  return {"roles":roles,"rules":r.get("rules",{}),"status":"evidence_required" if not self.evidence(r)=="evidence_backed" else "designed","radius_push_required":True,"decisions":self.decisions}
