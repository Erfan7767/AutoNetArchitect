from designers.fhrp.common import FHRPDesigner
class VRRPDesigner(FHRPDesigner):
 def design(self,r):
  groups=[{"vlan_id":x["vlan_id"],"version":r.get("version","v3"),"vrid":x.get("vrid",x["vlan_id"]),"virtual_ip":x.get("virtual_ip"),"priority":x.get("priority",100),"preempt":True,"advertisement":r.get("advertisement",1)} for x in r.get("vlans",[])]
  self.record_decision("vrrp_design",groups,"VRRP v3 supports dual-stack policy and multi-vendor deployment")
  return {"protocol":"vrrp","groups":groups,"evidence_status":self.evidence_status(r),"decisions":self.decisions}
