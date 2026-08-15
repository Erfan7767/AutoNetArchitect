from designers.base_designer import BaseDesigner
class DefaultRouteDesigner(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("default_source",[] if "routes" in "default_source" else "static");self.record_decision("default_source",value,"static routing policy with explicit next-hop and loop review")
  return {"default_source":value,"decisions":self.decisions,"assumptions":self.assumptions}
