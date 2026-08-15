from designers.fhrp.common import FHRPDesigner
class FHRPSTPAlignmentEnforcer(FHRPDesigner):
 def design(self,r):
  stp=r.get("stp_roots",{});fhrp=r.get("fhrp_active",{});matrix=[]
  for vlan in sorted(set(stp)|set(fhrp)):matrix.append({"vlan":vlan,"stp_root":stp.get(vlan),"fhrp_active":fhrp.get(vlan),"aligned":stp.get(vlan)==fhrp.get(vlan)})
  mis=[x for x in matrix if not x["aligned"]];self.record_decision("stp_fhrp_alignment",not mis,"default gateway active role follows STP root")
  return {"aligned":not mis,"matrix":matrix,"corrections":["align FHRP priority with STP root"] if mis else [],"decisions":self.decisions}
