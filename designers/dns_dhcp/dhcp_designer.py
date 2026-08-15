from designers.advanced_common import AdvancedDesigner
class DHCPDesigner(AdvancedDesigner):
    """Advanced design engine."""
    def design(self,r):
        scopes=r.get("scopes",[]);self.record_decision("dhcp",scopes,"scopes and relay targets are sourced from VLAN/IP plans")
        return {"status":"designed","scopes":scopes,"ha":len(r.get("servers",[]))>1,"relay_targets":r.get("relay_targets",[]),"source_of_truth":self.source(r),"decisions":self.decisions,"assumptions":self.assumptions}
