from designers.mpls.common import MPLSDesigner
class MPLSStrategySelector(MPLSDesigner):
    """MPLS design engine."""
    def design(self,r):
        offerings=self.mandatory(r,["sp_offerings"]);
        if r.get("sdwan_overlay"):strategy="mpls_sdwan_overlay"
        elif r.get("internal_mpls"):strategy="internal_mpls_limited"
        elif "l3vpn" in r.get("sp_offerings",[]):strategy="sp_l3vpn"
        elif "l2vpn" in r.get("sp_offerings",[]):strategy="sp_l2vpn"
        else:strategy="pending_sp_offering"
        self.record_decision("mpls_strategy",strategy,"strategy follows explicit provider offerings, SLA, scale, and migration intent");return {"strategy":strategy,"status":"blocked_missing_human_data" if offerings else "designed","decisions":self.decisions,"assumptions":self.assumptions}
