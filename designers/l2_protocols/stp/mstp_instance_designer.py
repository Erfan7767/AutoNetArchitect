from designers.l2_protocols.common import L2Designer
class MSTPInstanceDesigner(L2Designer):
 def design(self,r):
  mappings=r.get("instance_vlan_map",{}); self.record_decision("mst_region",r.get("region_name","site-region"),"consistent region identity is required on all switches")
  return {"region_name":r.get("region_name","site-region"),"revision":r.get("revision",1),"instance_vlan_map":mappings,"instance_count":len(mappings),"within_policy":len(mappings)<=16,"decisions":self.decisions}
