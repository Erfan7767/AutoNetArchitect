from designers.dr_bc.common import DRDesigner
class DRSiteDesigner(DRDesigner):
    """DR network design engine."""
    def design(self,r):
        missing=self.mandatory(r,["dr_location","dr_infrastructure"]);self.record_decision("dr_site",r.get("topology","different_subnets"),"routing-based DR with different subnets is preferred over L2 stretch");return {"status":"blocked_missing_human_data" if missing else "designed","location":r.get("dr_location"),"infrastructure":r.get("dr_infrastructure"),"topology":r.get("topology","different_subnets"),"equipment_model":r.get("equipment_model"),"security_zones":r.get("security_zones",[]),"decisions":self.decisions,"assumptions":self.assumptions}
