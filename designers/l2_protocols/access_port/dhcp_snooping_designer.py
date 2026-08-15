from designers.l2_protocols.common import L2Designer
class DHCPSnoopingDesigner(L2Designer):
 def design(self,r):
  value=r.get("trusted_ports",[]); prerequisite='None'; status="blocked_prerequisite" if prerequisite != "None" and not r.get(prerequisite,False) else "designed"; self.record_decision("trusted_ports",value,"role-based access safety policy")
  return {"status":status,"trusted_ports":value,"decisions":self.decisions}
