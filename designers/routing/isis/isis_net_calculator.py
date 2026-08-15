from designers.base_designer import BaseDesigner
class ISISNETCalculator(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("net",[] if "net" in ["levels","metrics"] else None);self.record_decision("isis_net",value,"IS-IS policy based on supplied topology and capability evidence")
  return {"net":value,"decisions":self.decisions,"assumptions":self.assumptions}
