from designers.cloud.common import CloudDesigner
class HybridRoutingDesigner(CloudDesigner):
    """Cloud connectivity design engine."""
    def design(self,r):
        self.record_decision("hybrid_routing",r.get("advertised_onprem_prefixes",[]),"route advertisements and preference protect against loops and asymmetry");return {"onprem_to_cloud":r.get("advertised_onprem_prefixes",[]),"cloud_to_onprem":r.get("advertised_cloud_prefixes",[]),"summary":r.get("summary_prefixes",[]),"preference":["dedicated","vpn"],"warnings":["asymmetric routing","overlapping prefixes","VPN/DX loops"],"decisions":self.decisions}
