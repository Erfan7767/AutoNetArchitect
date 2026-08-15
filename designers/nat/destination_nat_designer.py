from designers.nat.common import NATDesigner
class DestinationNATDesigner(NATDesigner):
 def design(self,r):
  rules=[];missing=[]
  for s in r.get("published_services",[]):
   if not s.get("public_ip"):missing.append("public_ip:"+str(s.get("name")));continue
   rules.append({"public_ip":s["public_ip"],"public_port":s.get("public_port"),"private_ip":s.get("private_ip"),"private_port":s.get("private_port"),"protocol":s.get("protocol","tcp")})
  for key in missing:self.record_assumption(key,None,"HumanSuppliedMandatory public service address")
  self.record_decision("destination_nat",rules,"published services require explicit public-to-private mapping")
  return {"status":"blocked_missing_human_data" if missing else "designed","rules":rules,"missing_human_mandatory":missing,"decisions":self.decisions,"assumptions":self.assumptions}
