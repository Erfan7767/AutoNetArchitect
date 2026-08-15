from designers.l2_protocols.common import L2Designer
class AllowedVLANPolicy(L2Designer):
 def design(self,r):
  allowed=list(r.get("required_vlans",[]));self.record_decision("allowed_vlans",allowed,"explicit allow-list; all is prohibited")
  return {"allowed_vlans":allowed,"all_prohibited":True,"pruning":True,"decisions":self.decisions}
