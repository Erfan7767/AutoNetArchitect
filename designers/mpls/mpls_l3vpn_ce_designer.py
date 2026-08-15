from designers.mpls.common import MPLSDesigner
class MPLSL3VPNCEDesigner(MPLSDesigner):
    """MPLS design engine."""
    def design(self,r):
        missing=self.mandatory(r,["pe_asn"]);protocol=r.get("routing_protocol","ebgp");self.record_decision("mpls_l3vpn_ce",protocol,"eBGP is preferred for SP-provided L3VPN; static/OSPF are explicit alternatives");return {"status":"blocked_missing_human_data" if missing else "designed","protocol":protocol,"ce_asn":r.get("ce_asn"),"pe_asn":r.get("pe_asn"),"advertised_prefixes":r.get("advertised_prefixes",[]),"received_prefixes":r.get("received_prefixes",[]),"vrfs":r.get("vrfs",[]),"filtering":True,"decisions":self.decisions,"assumptions":self.assumptions}
