from designers.cloud.common import CloudDesigner
class CloudVPNDesigner(CloudDesigner):
    """Cloud connectivity design engine."""
    def design(self,r):
        missing=self.mandatory(r,["provider","region","account_id","vpn_headend"]);count=2 if r.get("ha",True) else 1;self.record_decision("cloud_vpn",count,"HA uses two tunnels and BGP where supported");return {"status":"blocked_missing_human_data" if missing else "designed","provider":r.get("provider"),"region":r.get("region"),"account_id":r.get("account_id"),"tunnel_count":count,"routing":"bgp" if r.get("bgp",True) else "static","crypto":{"ike":"ikev2","encryption":"aes-256","integrity":"sha-256"},"source_of_truth":self.source(r),"decisions":self.decisions,"assumptions":self.assumptions}
