from designers.base_designer import BaseDesigner
class EIGRPMetricCalculator(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("metric",{} if "metric" in ["metric","authentication","timers"] else ([] if "metric" in ["summaries","stub_sites"] else True));self.record_decision("metric",value,"EIGRP policy from supplied requirements")
  return {"metric":value,"decisions":self.decisions,"assumptions":self.assumptions}
