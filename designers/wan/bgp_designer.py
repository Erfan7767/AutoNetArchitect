from designers.advanced_common import AdvancedDesigner
class BGPDesigner(AdvancedDesigner):
    """Advanced design engine."""
    def design(self,r):
        missing=self.mandatory(r,["local_asn","peer_asn","public_prefixes"]);self.record_decision("bgp",True,"external routing requires explicit ASN and prefix ownership")
        return {"status":"blocked_missing_human_data" if missing else "designed","local_asn":r.get("local_asn"),"peer_asn":r.get("peer_asn"),"public_prefixes":r.get("public_prefixes"),"source_of_truth":self.source(r),"decisions":self.decisions,"assumptions":self.assumptions}
