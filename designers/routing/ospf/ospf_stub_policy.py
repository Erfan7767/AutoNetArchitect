from designers.base_designer import BaseDesigner
class OSPFStubPolicy(BaseDesigner):
 def design(self,requirements):
  areas=[]
  for a in requirements.get("areas",[]):
   kind=a.get("type","regular");areas.append({"area":a.get("id"),"type":kind});self.record_decision(f"stub_{a.get('id')}",kind,"based on external-route and ASBR inputs")
  return {"areas":areas,"decisions":self.decisions}
