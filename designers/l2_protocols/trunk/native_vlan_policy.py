from designers.l2_protocols.common import L2Designer
class NativeVLANPolicy(L2Designer):
 def design(self,r):
  vlan=r.get("native_vlan",999);valid=vlan!=1 and vlan not in set(r.get("traffic_vlans",[]));self.record_decision("native_vlan",vlan,"unused native VLAN avoids user traffic and VLAN 1")
  return {"native_vlan":vlan,"valid":valid,"decisions":self.decisions}
