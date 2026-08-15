from designers.l2_protocols.common import L2Designer
class UnknownUnicastPolicy(L2Designer):
 def design(self,r):
  value=r.get("policy",[] if "features" in "policy" or "violations" in "policy" else {});self.record_decision("policy",value,"L2 safety and segmentation policy")
  return {"policy":value,"status":"blocked" if "violations" in "policy" and value else "designed","decisions":self.decisions}
