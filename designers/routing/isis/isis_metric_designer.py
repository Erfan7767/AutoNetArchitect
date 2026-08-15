from designers.base_designer import BaseDesigner
class ISISMetricDesigner(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("metrics",[] if "metrics" in ["levels","metrics"] else None);self.record_decision("isis_metrics",value,"IS-IS policy based on supplied topology and capability evidence")
  return {"metrics":value,"decisions":self.decisions,"assumptions":self.assumptions}
