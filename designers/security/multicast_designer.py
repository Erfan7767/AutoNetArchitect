from designers.advanced_common import AdvancedDesigner
class MulticastDesigner(AdvancedDesigner):
    """Advanced design engine."""
    def design(self,r):
        missing=self.mandatory(r,["rp_address"]) if r.get("multicast_enabled") else [];self.record_decision("multicast",r.get("multicast_enabled",False),"multicast is enabled only when RP and receiver intent are known")
        return {"status":"blocked_missing_human_data" if missing else "designed","rp_address":r.get("rp_address"),"igmp_snooping":r.get("igmp_snooping",True),"source_of_truth":self.source(r),"decisions":self.decisions,"assumptions":self.assumptions}
