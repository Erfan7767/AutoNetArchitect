from designers.dr_bc.common import DRDesigner
class DRCapacityPlanner(DRDesigner):
    """DR network design engine."""
    def design(self,r):
        normal=r.get("normal_bandwidth_mbps",0);active=r.get("production_bandwidth_mbps",0);self.record_decision("dr_capacity",active,"DR active mode is sized to production equivalent");return {"normal_bandwidth_mbps":normal,"active_bandwidth_mbps":active,"degraded_bandwidth_mbps":r.get("degraded_bandwidth_mbps",active//2 if isinstance(active,int) else None),"ports":r.get("ports"),"throughput":r.get("throughput"),"sessions":r.get("sessions"),"poe_budget_watts":r.get("poe_budget_watts"),"decisions":self.decisions}
