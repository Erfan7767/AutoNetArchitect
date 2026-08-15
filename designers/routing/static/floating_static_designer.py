from designers.base_designer import BaseDesigner
class FloatingStaticDesigner(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("floating_routes",[] if "routes" in "floating_routes" else "static");self.record_decision("floating_routes",value,"static routing policy with explicit next-hop and loop review")
  return {"floating_routes":value,"decisions":self.decisions,"assumptions":self.assumptions}
