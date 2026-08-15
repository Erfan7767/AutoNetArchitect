from designers.nat.common import NATDesigner
class NATHADesigner(NATDesigner):
 def design(self,r):
  stateful=bool(r.get("stateful_supported"));self.record_decision("nat_ha",stateful,"state synchronization determines failover continuity")
  return {"stateful":stateful,"session_sync":stateful,"shared_pool":bool(r.get("shared_pool")),"warning":None if stateful else "NAT session loss during failover is expected","decisions":self.decisions}
