from designers.l2_protocols.common import L2Designer
class MACAddressTablePolicy(L2Designer):
 def design(self,r):
  value=r.get("limits",[] if "features" in "limits" or "violations" in "limits" else {});self.record_decision("limits",value,"L2 safety and segmentation policy")
  return {"limits":value,"status":"blocked" if "violations" in "limits" and value else "designed","decisions":self.decisions}
