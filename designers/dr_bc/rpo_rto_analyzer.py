from designers.dr_bc.common import DRDesigner
class RPORTOAnalyzer(DRDesigner):
    """DR network design engine."""
    def design(self,r):
        services=r.get("services",[]);rows=[]
        for s in services:
            target_rpo=s.get("target_rpo");target_rto=s.get("target_rto");tech=s.get("replication_technology");missing=not tech;status="partial" if missing else "met";rows.append({"service_name":s.get("name"),"target_rpo":target_rpo,"target_rto":target_rto,"achievable_rpo":None if missing else target_rpo,"achievable_rto":None if missing else target_rto,"gap_status":status,"remediation_recommendation":"HumanSuppliedMandatory replication technology" if missing else None})
        self.record_decision("rpo_rto_analysis",rows,"achievability requires strategy, connectivity, and replication evidence");return {"rows":rows,"decisions":self.decisions}
