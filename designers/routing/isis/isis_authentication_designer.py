from designers.base_designer import BaseDesigner
class ISISAuthenticationDesigner(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("authentication",[] if "authentication" in ["levels","metrics"] else None);self.record_decision("isis_authentication",value,"IS-IS policy based on supplied topology and capability evidence")
  return {"authentication":value,"decisions":self.decisions,"assumptions":self.assumptions}
