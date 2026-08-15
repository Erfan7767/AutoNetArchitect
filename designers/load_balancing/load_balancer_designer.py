from designers.advanced_common import AdvancedDesigner
class LoadBalancerDesigner(AdvancedDesigner):
    """Design virtual services and pool health without inventing endpoints."""
    def design(self,r):
        missing=self.mandatory(r,["virtual_service_ip"])
        self.record_decision("load_balancer",r.get("virtual_service_ip"),"virtual service identity is explicit and pool members are supplied")
        return {"status":"blocked_missing_human_data" if missing else "designed","virtual_service_ip":r.get("virtual_service_ip"),"pools":r.get("pools",[]),"health_checks":r.get("health_checks",[]),"ha":len(r.get("nodes",[]))>1,"source_of_truth":self.source(r),"decisions":self.decisions,"assumptions":self.assumptions}
