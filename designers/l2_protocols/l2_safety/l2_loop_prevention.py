from designers.l2_protocols.common import L2Designer
class L2LoopPrevention(L2Designer):
 def design(self,r):
  value=r.get("features",[] if "features" in "features" or "violations" in "features" else {});self.record_decision("features",value,"L2 safety and segmentation policy")
  return {"features":value,"status":"blocked" if "violations" in "features" and value else "designed","decisions":self.decisions}
