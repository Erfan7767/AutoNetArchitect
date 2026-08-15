from designers.fhrp.common import FHRPDesigner
class HSRPDesigner(FHRPDesigner):
 def design(self,r):
  groups=[]
  for item in r.get("vlans",[]):
   vlan=item["vlan_id"];groups.append({"vlan_id":vlan,"version":r.get("version","v2"),"group":item.get("group",vlan),"virtual_ip":item.get("virtual_ip"),"hello":r.get("hello",1),"hold":r.get("hold",3),"multiple_groups":item.get("secondary_subnets",[])})
  self.record_decision("hsrp_design",groups,"HSRP v2 preferred with VLAN-derived group policy")
  return {"protocol":"hsrp","groups":groups,"evidence_status":self.evidence_status(r),"decisions":self.decisions}
