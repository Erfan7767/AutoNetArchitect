from designers.mpls.common import MPLSDesigner
class MPLSQoSMappingDesigner(MPLSDesigner):
    """MPLS design engine."""
    def design(self,r):
        missing=self.mandatory(r,["sp_cos_model"]);mapping=r.get("mapping",{"46":"EF","34":"AF41","18":"AF21","0":"BE"});self.record_decision("mpls_qos",mapping,"CE marking maps internal DSCP to SP SLA classes");return {"status":"blocked_missing_human_data" if missing else "designed","mapping":mapping,"class_model":r.get("sp_cos_model"),"decisions":self.decisions,"assumptions":self.assumptions}
