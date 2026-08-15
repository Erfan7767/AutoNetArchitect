from designers.mpls.common import MPLSDesigner
from .mpls_strategy_selector import MPLSStrategySelector
from .mpls_wan_ce_designer import MPLSWANCEDesigner
from .mpls_l3vpn_ce_designer import MPLSL3VPNCEDesigner
from .mpls_l2vpn_ce_designer import MPLSL2VPNCEDesigner
from .mpls_scope_boundary import MPLSScopeBoundary
class MPLSOrchestrator(MPLSDesigner):
    """Assemble CE-side MPLS design with explicit SP boundary."""
    def design(self,r):
        scope=MPLSScopeBoundary().design(r);strategy=MPLSStrategySelector().design(r);parts={"scope":scope,"strategy":strategy};s=strategy["strategy"]
        if s in {"sp_l3vpn","mpls_sdwan_overlay"}:parts["wan_ce"]=MPLSWANCEDesigner().design(r);parts["l3vpn"]=MPLSL3VPNCEDesigner().design(r)
        if s in {"sp_l2vpn","mpls_sdwan_overlay"}:parts["l2vpn"]=MPLSL2VPNCEDesigner().design(r)
        self.record_decision("mpls_orchestration",s,"strategy-driven CE-side artifact assembly");return {"artifact":"MPLSDesign","strategy":s,"parts":parts,"status":"designed","decisions":self.decisions}
