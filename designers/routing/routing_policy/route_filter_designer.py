from designers.base_designer import BaseDesigner
class RouteFilterDesigner(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("filters",[] if "distances" not in "filters" else {});self.record_decision("filters",value,"consistent routing policy intent")
  return {"filters":value,"decisions":self.decisions,"assumptions":self.assumptions}
