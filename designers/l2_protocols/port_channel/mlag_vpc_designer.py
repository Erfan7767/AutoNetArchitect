from designers.l2_protocols.common import L2Designer
class MLAGVPCDesigner(L2Designer):
 def design(self,r):
  vendor=r.get("vendor");supported={"Cisco":"vPC","Aruba":"VSX","Juniper":"MC-LAG"}.get(vendor);self.record_decision("multi_chassis_lag",supported,"vendor-specific MLAG selection")
  return {"status":"supported" if supported and self.supported(r) else "evidence_required","technology":supported,"peer_link":r.get("peer_link"),"peer_keepalive":r.get("peer_keepalive"),"decisions":self.decisions}
