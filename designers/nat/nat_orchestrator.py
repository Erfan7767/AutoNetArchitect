from designers.nat.common import NATDesigner
from .nat_strategy_selector import NATStrategySelector
from .pat_designer import PATDesigner
from .source_nat_designer import SourceNATDesigner
from .destination_nat_designer import DestinationNATDesigner
from .nat_exemption_designer import NATExemptionDesigner
class NATOrchestrator(NATDesigner):
 def design(self,r):
  strategy=NATStrategySelector().design(r);parts={"strategy":strategy};
  if "pat" in strategy["strategies"] or "policy_nat" in strategy["strategies"]:parts["source_nat"]=SourceNATDesigner().design(r);parts["pat"]=PATDesigner().design(r)
  if "destination_nat" in strategy["strategies"]:parts["destination_nat"]=DestinationNATDesigner().design(r)
  if "nat_exemption" in strategy["strategies"]:parts["exemption"]=NATExemptionDesigner().design(r)
  self.record_decision("nat_orchestration",strategy["strategies"],"strategy-driven NAT artifact assembly")
  return {"strategies":strategy["strategies"],"parts":parts,"status":"designed","decisions":self.decisions,"assumptions":self.assumptions}
