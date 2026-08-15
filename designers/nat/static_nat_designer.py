from designers.nat.common import NATDesigner
class StaticNATDesigner(NATDesigner):
 def design(self,r):
  entries=[];missing=[]
  for x in r.get("static_entries",[]):
   if not x.get("public_ip"):missing.append("public_ip");continue
   entries.append(x)
  self.record_decision("static_nat",entries,"1:1 translation is restricted to explicitly identified hosts")
  return {"status":"blocked_missing_human_data" if missing else "designed","entries":entries,"security_warning":"bidirectional exposure requires review","missing_human_mandatory":missing,"decisions":self.decisions}
