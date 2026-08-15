from designers.dr_bc.common import DRDesigner
from .dr_strategy_selector import DRStrategySelector
from .dr_site_designer import DRSiteDesigner
from .dr_connectivity_designer import DRConnectivityDesigner
from .dr_routing_designer import DRRoutingDesigner
from .dr_failover_designer import DRFailoverDesigner
from .dr_activation_planner import DRActivationPlanner
from .dr_scope_boundary import DRScopeBoundary
class DROrchestrator(DRDesigner):
    """Assemble network DR design and keep enterprise/application scope explicit."""
    def design(self,r):
        scope=DRScopeBoundary().design(r);strategy=DRStrategySelector().design(r);parts={"scope":scope,"strategy":strategy,"site":DRSiteDesigner().design(r),"connectivity":DRConnectivityDesigner().design(r),"routing":DRRoutingDesigner().design(r),"failover":DRFailoverDesigner().design(r),"activation":DRActivationPlanner().design({**r,"strategy":strategy["strategy"]})};self.record_decision("dr_orchestration",strategy["strategy"],"strategy, site, connectivity, routing, failover, and activation are assembled in dependency order");return {"artifact":"DRDesign","parts":parts,"status":"designed","decisions":self.decisions}
