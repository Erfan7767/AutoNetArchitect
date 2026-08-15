from designers.cloud.common import CloudDesigner
class HybridDNSDesigner(CloudDesigner):
    """Cloud connectivity design engine."""
    def design(self,r):
        missing=self.mandatory(r,["dns_server_ips"]);self.record_decision("hybrid_dns",r.get("direction","bidirectional"),"conditional forwarding connects on-prem and cloud DNS");return {"status":"blocked_missing_human_data" if missing else "designed","direction":r.get("direction","bidirectional"),"dns_server_ips":r.get("dns_server_ips"),"provider_service":r.get("provider_service"),"decisions":self.decisions,"assumptions":self.assumptions}
