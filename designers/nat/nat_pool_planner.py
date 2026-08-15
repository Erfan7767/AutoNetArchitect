from designers.nat.common import NATDesigner
class NATPoolPlanner(NATDesigner):
 def design(self,r):
  missing=self.required_public_data(r,["pool_start","pool_end"]);pool=None if missing else {"start":r["pool_start"],"end":r["pool_end"],"type":r.get("pool_type","overload"),"isp":r.get("isp")};self.record_decision("nat_pool",pool,"public pools are explicit human-supplied inputs")
  return {"status":"blocked_missing_human_data" if missing else "designed","pool":pool,"missing_human_mandatory":missing,"decisions":self.decisions,"assumptions":self.assumptions}
