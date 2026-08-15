from designers.dr_bc.common import DRDesigner
class DRRoutingDesigner(DRDesigner):
    """DR network design engine."""
    def design(self,r):
        self.record_decision("dr_routing",r.get("protocol","bgp"),"primary routes are preferred normally and DR routes become preferred on failover");return {"protocol":r.get("protocol","bgp"),"normal_preference":"primary","failover_preference":"dr","mechanisms":["route_withdrawal","as_path_prepend","floating_static"],"runbook_required":True,"decisions":self.decisions}
