from designers.cloud.common import CloudDesigner
from .cloud_strategy_selector import CloudStrategySelector
from .cloud_vpn_designer import CloudVPNDesigner
from .direct_connect_designer import DirectConnectDesigner
from .expressroute_designer import ExpressRouteDesigner
from .cloud_interconnect_designer import CloudInterconnectDesigner
from .cloud_scope_boundary import CloudScopeBoundary
class CloudOrchestrator(CloudDesigner):
    """Assemble on-premises to cloud connectivity design."""
    def design(self,r):
        scope=CloudScopeBoundary().design(r);strategy=CloudStrategySelector().design(r);method=strategy["method"];parts={"scope":scope,"strategy":strategy}
        if method in {"vpn","hybrid"}:parts["vpn"]=CloudVPNDesigner().design(r)
        if r.get("provider")=="aws" and method in {"dedicated","hybrid"}:parts["direct_connect"]=DirectConnectDesigner().design(r)
        if r.get("provider")=="azure" and method in {"dedicated","hybrid"}:parts["expressroute"]=ExpressRouteDesigner().design(r)
        if r.get("provider")=="gcp" and method in {"dedicated","hybrid"}:parts["interconnect"]=CloudInterconnectDesigner().design(r)
        self.record_decision("cloud_orchestration",method,"strategy-selected connectivity artifact with explicit scope boundary");return {"artifact":"CloudConnectivityDesign","method":method,"parts":parts,"status":"designed","decisions":self.decisions}
