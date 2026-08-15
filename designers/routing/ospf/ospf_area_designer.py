from designers.base_designer import BaseDesigner
class OSPFAreaDesigner(BaseDesigner):
 def design(self,requirements):
  areas=requirements.get("areas",[{"id":0,"type":"regular","sites":[]}]);
  for area in areas:self.record_decision(f"area_{area.get('id')}",area.get("type","regular"),"area type follows supplied topology and external-route intent")
  return {"areas":areas,"lsa_estimate":sum(max(1,len(a.get("sites",[]))*10) for a in areas),"decisions":self.decisions}
