"""Interior routing orchestration."""
from designers.base_designer import BaseDesigner
from .routing_strategy_selector import RoutingStrategySelector
from .ospf.ospf_designer import OSPFDesigner
from .eigrp.eigrp_designer import EIGRPDesigner
from .isis.isis_designer import ISISDesigner
class RoutingOrchestrator(BaseDesigner):
    """Coordinate one IGP and preserve decision/assumption auditability."""
    def design(self,requirements):
        selection=RoutingStrategySelector().design(requirements); protocol=selection["protocol"]
        if protocol=="ospf": result=OSPFDesigner().design(requirements)
        elif protocol=="eigrp": result=EIGRPDesigner().design(requirements)
        elif protocol=="isis": result=ISISDesigner().design(requirements)
        else: result={"protocol":"static","status":"static_only"}
        self.record_decision("orchestration",protocol,"one IGP selected to avoid conflicting interior control planes")
        return {"selected":selection,"design":result,"decisions":self.decisions,"assumptions":self.assumptions,"conflict_check":"single_igp"}
