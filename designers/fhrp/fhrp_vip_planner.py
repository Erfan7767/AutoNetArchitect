from designers.fhrp.common import FHRPDesigner
import ipaddress
class FHRPVIPPlanner(FHRPDesigner):
 def design(self,r):
  plans=[];used=set(r.get("used_ips",[]));
  for subnet in r.get("subnets",[]):
   network=ipaddress.ip_network(subnet,strict=False); policy=r.get("vip_policy","first_usable"); candidates=list(network.hosts());vip=str(candidates[0] if policy=="first_usable" else candidates[-1]) if candidates else None;conflict=vip in used if vip else True;plans.append({"subnet":subnet,"vip":vip,"conflict":conflict,"dhcp_default_gateway":vip})
  self.record_decision("vip_policy",r.get("vip_policy","first_usable"),"VIP is derived from supplied subnet and reserved away from physical addresses")
  return {"plans":plans,"conflicts":[p for p in plans if p["conflict"]],"decisions":self.decisions}
