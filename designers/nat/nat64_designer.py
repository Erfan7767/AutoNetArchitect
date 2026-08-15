from designers.nat.common import NATDesigner
class NAT64Designer(NATDesigner):
 def design(self,r):
  enabled=bool(r.get("ipv6_transition"));status="optional_not_requested" if not enabled else "evidence_required" if not self.supported(r) else "designed";self.record_decision("nat64",enabled,"NAT64 is optional and requires platform evidence plus DNS64")
  return {"status":status,"dns64_required":enabled,"stateful":enabled,"decisions":self.decisions}
