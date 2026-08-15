from designers.base_designer import BaseDesigner
class EIGRPStubPolicy(BaseDesigner):
 def design(self,requirements):
  value=requirements.get("stub_sites",{} if "stub_sites" in ["metric","authentication","timers"] else ([] if "stub_sites" in ["summaries","stub_sites"] else True));self.record_decision("stub_sites",value,"EIGRP policy from supplied requirements")
  return {"stub_sites":value,"decisions":self.decisions,"assumptions":self.assumptions}
