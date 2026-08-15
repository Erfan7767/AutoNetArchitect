from designers.l2_protocols.common import L2Designer
class IPSGDesigner(L2Designer):
 def design(self,r):
  value=r.get("ports",[]); prerequisite='dhcp_snooping_enabled'; status="blocked_prerequisite" if prerequisite != "None" and not r.get(prerequisite,False) else "designed"; self.record_decision("ports",value,"role-based access safety policy")
  return {"status":status,"ports":value,"decisions":self.decisions}
