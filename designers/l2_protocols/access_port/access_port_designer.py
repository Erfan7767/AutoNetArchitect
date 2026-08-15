from designers.l2_protocols.common import L2Designer
class AccessPortDesigner(L2Designer):
 def design(self,r):
  roles=r.get("roles",[]);configs=[{"interface":x.get("interface"),"role":x.get("role"),"data_vlan":x.get("data_vlan"),"voice_vlan":x.get("voice_vlan"),"portfast":True,"bpdu_guard":True} for x in roles];self.record_decision("access_ports",configs,"role-based edge protection and VLAN assignment")
  return {"ports":configs,"decisions":self.decisions}
