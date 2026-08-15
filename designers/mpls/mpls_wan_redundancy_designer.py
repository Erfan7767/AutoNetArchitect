from designers.mpls.common import MPLSDesigner
class MPLSWANRedundancyDesigner(MPLSDesigner):
    """MPLS design engine."""
    def design(self,r):
        diversity=self.mandatory(r,["sp_path_diversity_confirmation"]) if r.get("dual_homed") else [];self.record_decision("mpls_redundancy",r.get("dual_homed",False),"dual PE and diverse paths are accepted only with SP confirmation");return {"status":"blocked_missing_human_data" if diversity else "designed","dual_homed":bool(r.get("dual_homed")),"path_policy":r.get("path_policy","primary_backup"),"backup_transport":r.get("backup_transport","internet_vpn"),"decisions":self.decisions,"assumptions":self.assumptions}
