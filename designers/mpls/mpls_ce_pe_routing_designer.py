from designers.mpls.common import MPLSDesigner
class MPLSCEPERoutingDesigner(MPLSDesigner):
    """MPLS design engine."""
    def design(self,r):
        self.record_decision("mpls_ce_pe_routing",r.get("routing_protocol","ebgp"),"CE advertises site-specific prefixes and filters unexpected routes");return {"protocol":r.get("routing_protocol","ebgp"),"outbound_filter":"local_prefixes_only","inbound_filter":"reject_unexpected","default_route_received":r.get("accept_default",True),"dual_homed_policy":r.get("dual_homed_policy","primary_backup"),"as_path_prepend_secondary":True,"decisions":self.decisions}
