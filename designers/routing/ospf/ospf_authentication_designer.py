from designers.base_designer import BaseDesigner
class OSPFAuthenticationDesigner(BaseDesigner):
 def design(self,requirements):
  method=requirements.get("method","sha");self.record_assumption("key_rotation","operator-managed schedule","key lifetime was not supplied") if "key_rotation" not in requirements else None
  self.record_decision("ospf_authentication",method,"selected from platform capability evidence when supplied")
  return {"method":method,"scope":requirements.get("scope","interface"),"key_rotation":requirements.get("key_rotation"),"evidence_required":not bool(requirements.get("evidence_ids")),"decisions":self.decisions,"assumptions":self.assumptions}
