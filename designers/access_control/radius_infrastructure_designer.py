from designers.access_control.common import NACDesigner
class RadiusInfrastructureDesigner(NACDesigner):
 def design(self,r):
  missing=self.mandatory(r,["radius_server_type","radius_servers"]);self.record_decision("radius_infrastructure",r.get("radius_servers"),"primary/secondary RADIUS infrastructure is explicit")
  return {"status":"blocked_missing_human_data" if missing else "designed","server_type":r.get("radius_server_type"),"servers":r.get("radius_servers"),"auth_port":1812,"accounting_port":1813,"ha":len(r.get("radius_servers",[]))>1,"missing_human_mandatory":missing,"decisions":self.decisions,"assumptions":self.assumptions}
