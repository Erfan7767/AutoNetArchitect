from designers.base_designer import BaseDesigner
class ISISDesigner(BaseDesigner):
 def design(self,requirements):
  net=requirements.get("isis_net");
  if net is None:self.record_assumption("isis_net","policy_required","NET must be assigned from approved addressing policy")
  self.record_decision("isis_deployment",True,"IS-IS selected by explicit strategy")
  return {"protocol":"isis","net":net,"levels":requirements.get("isis_levels",["L1/L2"]),"wide_metrics":True,"decisions":self.decisions,"assumptions":self.assumptions}
