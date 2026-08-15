from designers.base_designer import BaseDesigner
from .ospf_area_designer import OSPFAreaDesigner
from .ospf_cost_calculator import OSPFCostCalculator
class OSPFDesigner(BaseDesigner):
 def design(self,requirements):
  pid=requirements.get("process_id");rid=requirements.get("router_id")
  if pid is None:self.record_assumption("process_id","policy_required","process ID is not universal and must be approved")
  if rid is None:self.record_assumption("router_id","loopback_required","router ID must come from an approved loopback")
  self.record_decision("ospf_deployment",True,"OSPF selected by routing strategy")
  return {"protocol":"ospf","process_id":pid,"router_id":rid,"areas":OSPFAreaDesigner().design(requirements),"costs":OSPFCostCalculator().design(requirements),"reference_bandwidth_mbps":requirements.get("reference_bandwidth_mbps"),"asbrs":requirements.get("asbrs",[]),"decisions":self.decisions,"assumptions":self.assumptions}
