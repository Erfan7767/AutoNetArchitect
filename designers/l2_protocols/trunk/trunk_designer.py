from designers.l2_protocols.common import L2Designer
class TrunkDesigner(L2Designer):
 def design(self,r):
  allowed=r.get("allowed_vlans",[]);native=r.get("native_vlan",999);self.record_decision("trunks",{"allowed_vlans":allowed,"native_vlan":native,"encapsulation":"dot1q"},"least privilege trunking with dot1q")
  return {"allowed_vlans":allowed,"native_vlan":native,"encapsulation":"dot1q","decisions":self.decisions}
