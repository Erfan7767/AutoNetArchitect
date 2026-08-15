from designers.base_designer import BaseDesigner
class ISISLevelDesigner(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("levels",[] if "levels" in ["levels","metrics"] else None);self.record_decision("isis_levels",value,"IS-IS policy based on supplied topology and capability evidence")
  return {"levels":value,"decisions":self.decisions,"assumptions":self.assumptions}
