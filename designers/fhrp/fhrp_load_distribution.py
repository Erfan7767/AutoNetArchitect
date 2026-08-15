from designers.fhrp.common import FHRPDesigner
class FHRPLoadDistribution(FHRPDesigner):
 def design(self,r):
  vlan_ids=r.get("vlan_ids",[]);counts={"switch_a":sum(v%2 for v in vlan_ids),"switch_b":sum(1 for v in vlan_ids if v%2==0)};imbalance=abs(counts["switch_a"]-counts["switch_b"]);self.record_decision("fhrp_load_distribution",counts,"odd/even active split")
  return {"active_vlan_counts":counts,"imbalance":imbalance,"balanced":imbalance<=1,"decisions":self.decisions}
