from designers.advanced_common import AdvancedDesigner
class IPv6Designer(AdvancedDesigner):
    """Advanced design engine."""
    def design(self,r):
        prefix=r.get("ipv6_prefix");missing=self.mandatory(r,["ipv6_prefix"])
        self.record_decision("ipv6_dual_stack",True,"dual-stack preserves IPv4 reachability while IPv6 is introduced")
        return {"status":"blocked_missing_human_data" if missing else "designed","ipv6_prefix":prefix,"dual_stack":True,"subnets":r.get("subnets",[]),"source_of_truth":self.source(r),"decisions":self.decisions,"assumptions":self.assumptions}
