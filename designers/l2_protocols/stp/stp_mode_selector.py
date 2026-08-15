from designers.l2_protocols.common import L2Designer
class STPModeSelector(L2Designer):
 def design(self,r):
  vendors=set(r.get("vendors",[])); vlans=int(r.get("vlan_count",0)); multi=bool(r.get("multi_vendor"));
  mode="mstp" if multi or vlans>100 else "rapid_pvst_plus" if "Cisco" in vendors else "mstp"
  self.record_decision("stp_mode",mode,"multi-vendor or scale policy selects standards-based MSTP; Cisco campus selects Rapid-PVST+")
  return {"mode":mode,"evidence_status":self.evidence_status(r),"alternatives":["pvst_plus","rapid_pvst_plus","mstp"],"decisions":self.decisions}
