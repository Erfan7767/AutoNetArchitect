from designers.base_designer import BaseDesigner
class StaticRouteDesigner(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("routes",[] if "routes" in "routes" else "static");self.record_decision("routes",value,"static routing policy with explicit next-hop and loop review")
  return {"routes":value,"decisions":self.decisions,"assumptions":self.assumptions}
