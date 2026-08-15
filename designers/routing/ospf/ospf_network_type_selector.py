from designers.base_designer import BaseDesigner
class OSPFNetworkTypeSelector(BaseDesigner):
 def design(self,requirements):
  links=requirements.get("links",[]);out=[]
  for l in links:
   typ=l.get("type","broadcast");typ="point_to_point" if l.get("inter_router") else typ;out.append({"interface":l.get("interface"),"network_type":typ});self.record_decision(f"network_{l.get('interface')}",typ,"inter-router links use point-to-point; Ethernet defaults to broadcast")
  return {"interfaces":out,"decisions":self.decisions}
