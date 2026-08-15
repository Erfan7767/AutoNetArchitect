from designers.fhrp.common import FHRPDesigner
class FHRPPreemptionPolicy(FHRPDesigner):
 def design(self,r):
  policy={"enabled":r.get("preempt",True),"reload_delay":r.get("reload_delay",60),"minimum_delay":r.get("minimum_delay",30)};self.record_decision("preemption",policy,"deterministic failback with reload protection")
  return {"policy":policy,"warning":None if policy["reload_delay"] else "preemption requires reload delay","decisions":self.decisions}
