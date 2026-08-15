from designers.nat.common import NATDesigner
class PolicyNATDesigner(NATDesigner):
 def design(self,r):
  policies=r.get("policies",[]);self.record_decision("policy_nat",policies,"policy selects translation by ISP, source segment, or application")
  return {"policies":policies,"dual_isp":bool(r.get("dual_isp")),"decisions":self.decisions}
