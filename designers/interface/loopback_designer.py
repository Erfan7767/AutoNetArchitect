from designers.interface.common import InterfaceDesigner
class LoopbackDesigner(InterfaceDesigner):
    """Design loopback roles using supplied loopback addresses."""
    def design(self,r):
        loops=[{"interface":f"Loopback{x.get('number',0)}","purpose":x.get("purpose","router_id"),"ip":x.get("ip")} for x in r.get("loopbacks",[])];self.record_decision("loopbacks",loops,"loopback purpose and address come from the IP plan");return {"loopbacks":loops,"decisions":self.decisions}
