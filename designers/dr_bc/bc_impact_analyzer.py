from designers.dr_bc.common import DRDesigner
class BCImpactAnalyzer(DRDesigner):
    """DR network design engine."""
    def design(self,r):
        components=r.get("components",[]);matrix=[]
        for c in components:matrix.append({"component":c.get("name"),"type":c.get("type"),"impact":c.get("impact","partial_outage"),"single_point_of_failure":not c.get("redundant",False)})
        self.record_decision("bc_impact",matrix,"impact follows component scope and redundancy metadata");return {"matrix":matrix,"decisions":self.decisions}
