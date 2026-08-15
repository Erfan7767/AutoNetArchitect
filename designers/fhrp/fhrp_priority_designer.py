from designers.fhrp.common import FHRPDesigner
class FHRPPriorityDesigner(FHRPDesigner):
 def design(self,r):
  priorities={};
  for vlan in r.get("vlan_ids",[]):priorities[vlan]={"switch_a":110 if vlan%2 else 100,"switch_b":100 if vlan%2 else 110}
  self.record_decision("fhrp_priorities",priorities,"odd/even VLAN split distributes active gateways")
  return {"priorities":priorities,"decisions":self.decisions}
