from designers.base_designer import BaseDesigner
class EIGRPAuthenticationDesigner(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("authentication",{} if "authentication" in ["metric","authentication","timers"] else ([] if "authentication" in ["summaries","stub_sites"] else True));self.record_decision("authentication",value,"EIGRP policy from supplied requirements")
  return {"authentication":value,"decisions":self.decisions,"assumptions":self.assumptions}
