from designers.cloud.common import CloudDesigner
class HybridIPPlanner(CloudDesigner):
    """Cloud connectivity design engine."""
    def design(self,r):
        missing=self.mandatory(r,["cloud_cidrs"]);all_ranges=list(r.get("onprem_cidrs",[]))+list(r.get("cloud_cidrs",[]))+list(r.get("tunnel_cidrs",[]));overlap=len(all_ranges)!=len(set(all_ranges));self.record_decision("hybrid_ip",all_ranges,"overlap detection uses explicit on-prem, cloud, tunnel, and peering ranges");return {"status":"blocked_missing_human_data" if missing else "blocked_overlap" if overlap else "designed","ranges":all_ranges,"overlap":overlap,"bgp_peering_ranges":r.get("bgp_peering_ranges",[]),"decisions":self.decisions,"assumptions":self.assumptions}
