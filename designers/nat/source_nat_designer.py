from designers.nat.common import NATDesigner
class SourceNATDesigner(NATDesigner):
 def design(self,r):
  missing=self.required_public_data(r,["outside_interface"]);rules=[]
  if not missing:
   rules=[{"inside_zone":r.get("inside_zone","inside"),"outside_zone":r["outside_interface"],"mode":"pool" if r.get("nat_pool") else "pat","pool":r.get("nat_pool")}]
  self.record_decision("source_nat",rules,"inside-to-outside translation with platform order awareness")
  return {"status":"blocked_missing_human_data" if missing else "designed","rules":rules,"missing_human_mandatory":missing,"vendor_order_awareness":True,"decisions":self.decisions,"assumptions":self.assumptions}
