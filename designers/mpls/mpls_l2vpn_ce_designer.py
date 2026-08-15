from designers.mpls.common import MPLSDesigner
class MPLSL2VPNCEDesigner(MPLSDesigner):
    """MPLS design engine."""
    def design(self,r):
        service=r.get("service_type","e-line");self.record_decision("mpls_l2vpn_ce",service,"CE presents an L2 service while SP-side VPLS/VPWS remains out of scope");return {"status":"designed","service":service,"interface_mode":r.get("interface_mode","trunk"),"vlan_mapping":r.get("vlan_mapping",{}),"warnings":["STP over L2VPN is normally disabled","broadcast domain extension risk"],"decisions":self.decisions}
