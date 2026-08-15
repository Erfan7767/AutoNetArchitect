from designers.advanced_common import AdvancedDesigner
from .dns_designer import DNSDesigner
from .dhcp_designer import DHCPDesigner
class DNSDHCPDesigner(AdvancedDesigner):
    """Coordinate DNS and DHCP with HA awareness."""
    def design(self,r):
        dns=DNSDesigner().design(r);dhcp=DHCPDesigner().design(r);self.record_decision("dns_dhcp",True,"DNS and DHCP artifacts share the source of truth");return {"dns":dns,"dhcp":dhcp,"ha":dns["ha"] and dhcp["ha"],"source_of_truth":self.source(r),"decisions":self.decisions}
