from designers.access_control.common import NACDesigner
from .dot1x_strategy_selector import Dot1XStrategySelector
from .radius_infrastructure_designer import RadiusInfrastructureDesigner
from .dot1x_wired_designer import Dot1XWiredDesigner
from .dot1x_wireless_designer import Dot1XWirelessDesigner
from .deployment_phasing_planner import DeploymentPhasingPlanner
class NACOrchestrator(NACDesigner):
 def design(self,r):
  required=bool(r.get("nac_required",r.get("regulated_domain",False)));strategy=Dot1XStrategySelector().design(r) if required else {"strategy":"not_required","phases":[]};radius=RadiusInfrastructureDesigner().design(r) if required else {"status":"not_required"};wired=Dot1XWiredDesigner().design(r) if required else {"status":"not_required"};wireless=Dot1XWirelessDesigner().design(r) if required else {"status":"not_required"};phasing=DeploymentPhasingPlanner().design(r) if required else {"phases":[]};self.record_decision("nac_orchestration",required,"NAC requirement follows explicit requirement or regulated domain");return {"required":required,"strategy":strategy,"radius":radius,"wired":wired,"wireless":wireless,"phasing":phasing,"artifact":"NACDesign","decisions":self.decisions,"assumptions":self.assumptions}
