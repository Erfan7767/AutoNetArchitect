from designers.fhrp.common import FHRPDesigner
class GLBPDesigner(FHRPDesigner):
 def design(self,r):
  if set(r.get("vendors",[]))!={"Cisco"}:return {"status":"blocked_vendor_scope","reason":"GLBP is Cisco proprietary","decisions":self.decisions}
  self.record_decision("glbp_design",r.get("groups",[]),"Cisco-only AVG/AVF distribution")
  return {"protocol":"glbp","groups":r.get("groups",[]),"load_balance":r.get("load_balance","round-robin"),"weighting":r.get("weighting",{}),"decisions":self.decisions}
