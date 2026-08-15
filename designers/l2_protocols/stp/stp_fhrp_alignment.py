from designers.l2_protocols.common import L2Designer
class STPFHRPAlignment(L2Designer):
 def design(self,r):
  stp=r.get("stp_roots",{}); fhrp=r.get("fhrp_active",{}); mis=[vlan for vlan in set(stp)|set(fhrp) if stp.get(vlan)!=fhrp.get(vlan)]; self.record_decision("fhrp_alignment",not mis,"STP root should align with FHRP active gateway")
  return {"aligned":not mis,"misaligned_vlans":mis,"corrections":["move STP root or FHRP active role" ] if mis else [],"decisions":self.decisions}
