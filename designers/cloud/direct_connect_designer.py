from designers.cloud.common import CloudDesigner
class DirectConnectDesigner(CloudDesigner):
    """Cloud connectivity design engine."""
    def design(self,r):
        missing=self.mandatory(r,["provider","region","account_id","location"]);self.record_decision("direct_connect",r.get("connection_type","dedicated"),"AWS dedicated or hosted connection with explicit location and VIFs");return {"status":"blocked_missing_human_data" if missing else "designed","connection_type":r.get("connection_type","dedicated"),"location":r.get("location"),"vifs":r.get("vifs",["private"]),"customer_asn":r.get("customer_asn"),"aws_asn":r.get("aws_asn"),"ha":bool(r.get("dual_connections")),"decisions":self.decisions,"assumptions":self.assumptions}
