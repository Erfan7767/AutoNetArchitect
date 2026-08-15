from designers.l2_protocols.common import L2Designer
class STPRootDesigner(L2Designer):
 def design(self,r):
  roots=r.get("roots",{}); access=set(r.get("access_switches",[])); invalid=access & set(roots.values());
  if invalid:self.record_assumption("root_review",sorted(invalid),"access switches cannot be STP roots")
  self.record_decision("stp_roots",roots,"roots follow core/distribution traffic flow")
  return {"roots":roots,"invalid_access_roots":sorted(invalid),"decisions":self.decisions,"assumptions":self.assumptions}
