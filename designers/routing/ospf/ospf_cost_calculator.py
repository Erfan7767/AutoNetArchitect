from designers.base_designer import BaseDesigner
class OSPFCostCalculator(BaseDesigner):
 def design(self,requirements):
  ref=requirements.get("reference_bandwidth_mbps"); links=requirements.get("links",[]);
  if ref is None:self.record_assumption("reference_bandwidth_mbps",100000,"policy value required to avoid platform default drift")
  costs=[{"link":l.get("name"),"cost":max(1,round(ref/(l.get("bandwidth_mbps") or 1)))} for l in links] if ref else []
  self.record_decision("ospf_cost_policy",ref,"reference bandwidth with explicit link calculations")
  return {"reference_bandwidth_mbps":ref,"costs":costs,"equal_cost_groups":[],"suboptimal_paths":[],'decisions':self.decisions,'assumptions':self.assumptions}
