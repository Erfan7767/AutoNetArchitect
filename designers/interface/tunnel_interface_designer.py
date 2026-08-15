from designers.interface.common import InterfaceDesigner
class TunnelInterfaceDesigner(InterfaceDesigner):
    """Design GRE, IPsec, and VXLAN tunnel interface metadata."""
    def design(self,r):
        tunnels=[{"interface":f"Tunnel{x.get('id',0)}","mode":x.get("mode","gre"),"source":x.get("source"),"destination":x.get("destination"),"ip":x.get("ip")} for x in r.get("tunnels",[])];self.record_decision("tunnels",tunnels,"tunnel endpoints and source are explicit");return {"tunnels":tunnels,"decisions":self.decisions}
