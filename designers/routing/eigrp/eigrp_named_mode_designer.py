from designers.base_designer import BaseDesigner
class EIGRPNamedModeDesigner(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("named_mode",{} if "named_mode" in ["metric","authentication","timers"] else ([] if "named_mode" in ["summaries","stub_sites"] else True));self.record_decision("named_mode",value,"EIGRP policy from supplied requirements")
  return {"named_mode":value,"decisions":self.decisions,"assumptions":self.assumptions}
