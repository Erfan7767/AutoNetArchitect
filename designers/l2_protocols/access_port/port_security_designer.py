from designers.l2_protocols.common import L2Designer
class PortSecurityDesigner(L2Designer):
 def design(self,r):
  value=r.get("max_mac",1); prerequisite='None'; status="blocked_prerequisite" if prerequisite != "None" and not r.get(prerequisite,False) else "designed"; self.record_decision("max_mac",value,"role-based access safety policy")
  return {"status":status,"max_mac":value,"decisions":self.decisions}
