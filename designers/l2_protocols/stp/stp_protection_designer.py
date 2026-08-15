from designers.l2_protocols.common import L2Designer
class STPProtectionDesigner(L2Designer):
 MAP={"Cisco":{"root_guard":"spanning-tree guard root","bpdu_guard":"spanning-tree bpduguard","loop_guard":"spanning-tree guard loop","udld":"udld enable"},"Aruba":{"root_guard":"root-guard","bpdu_guard":"bpdu-protection","loop_guard":"loop-protect","udld":"udld"},"Huawei":{"root_guard":"stp root-protection","bpdu_guard":"stp bpdu-protection","loop_guard":"stp loop-protection","udld":"udld enable"},"Juniper":{"root_guard":"root-protect","bpdu_guard":"bpdu-block","loop_guard":"loop-protect","udld":"udld"}}
 def design(self,r):
  vendor=r.get("vendor","unknown"); features=self.MAP.get(vendor); status="evidence_required" if not self.supported(r) else "supported"
  self.record_decision("stp_protection",features or {},"role-based protection with vendor command mapping")
  return {"status":status,"vendor":vendor,"features":features,"bpdu_filter_warning":True,"decisions":self.decisions}
