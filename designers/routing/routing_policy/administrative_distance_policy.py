from designers.base_designer import BaseDesigner
class AdministrativeDistancePolicy(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("administrative_distances",[] if "distances" not in "administrative_distances" else {});self.record_decision("administrative_distances",value,"consistent routing policy intent")
  return {"administrative_distances":value,"decisions":self.decisions,"assumptions":self.assumptions}
