from designers.nat.common import NATDesigner
class NATLoggingPolicy(NATDesigner):
 def design(self,r):
  policy={"translations_created":True,"translations_deleted":True,"rate":r.get("rate","sampled"),"retention_days":r.get("retention_days",90),"compliance":r.get("compliance",[])};self.record_decision("nat_logging",policy,"translation auditability with performance awareness")
  return {"policy":policy,"pci_required":"PCI" in policy["compliance"],"decisions":self.decisions}
