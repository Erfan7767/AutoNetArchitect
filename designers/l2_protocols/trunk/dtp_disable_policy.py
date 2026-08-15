from designers.l2_protocols.common import L2Designer
class DTPDisablePolicy(L2Designer):
 def design(self,r):
  vendor=r.get("vendor","Cisco");command={"Cisco":"switchport nonegotiate","Aruba":"disable-dtp","Huawei":"undo negotiation auto"}.get(vendor);self.record_decision("dtp_disable",command,"DTP is disabled on explicit trunks")
  return {"vendor":vendor,"command":command,"access_mode":"access","decisions":self.decisions}
