from designers.cloud.common import CloudDesigner
class HybridSecurityDesigner(CloudDesigner):
    """Cloud connectivity design engine."""
    def design(self,r):
        self.record_decision("hybrid_security",r.get("inspection","onprem_firewall"),"on-premises cloud-bound inspection is in scope");return {"inspection":r.get("inspection","onprem_firewall"),"vpn_encrypted":True,"direct_connect_encryption":r.get("macsec_or_overlay",False),"cloud_side_nva":"out_of_scope_v1","cloud_security_groups":"out_of_scope_v1","decisions":self.decisions}
