from designers.advanced_common import AdvancedDesigner
class DNSDesigner(AdvancedDesigner):
    """Advanced design engine."""
    def design(self,r):
        servers=r.get("servers",[]);self.record_decision("dns",servers,"authoritative and recursive roles are explicit")
        return {"status":"designed","servers":servers,"ha":len(servers)>1,"split_horizon":r.get("split_horizon",False),"source_of_truth":self.source(r),"decisions":self.decisions,"assumptions":self.assumptions}
