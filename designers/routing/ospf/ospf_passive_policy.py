from designers.base_designer import BaseDesigner
class OSPFPassivePolicy(BaseDesigner):
 def design(self,requirements):
  passive=list(requirements.get("access_interfaces",[]))+list(requirements.get("management_interfaces",[]));nonpassive=list(requirements.get("routing_interfaces",[]));self.record_decision("passive_default",True,"passive by default with explicit routing links")
  return {"passive":passive,"non_passive":nonpassive,"decisions":self.decisions}
