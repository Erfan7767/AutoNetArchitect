from designers.nat.common import NATDesigner
class NATStrategySelector(NATDesigner):
 def design(self,r):
  strategies=[];rejections={};
  if r.get("internet_access"):strategies.append("pat" if not r.get("dual_isp") else "policy_nat")
  if r.get("published_servers"):strategies.extend(["destination_nat","static_nat"])
  if r.get("vpn_tunnels"):strategies.append("nat_exemption")
  if r.get("overlapping_addresses"):strategies.append("policy_nat")
  if r.get("ipv6_transition"):strategies.append("nat64")
  self.record_decision("nat_strategy",strategies,"strategy follows internet, publication, VPN, overlap, ISP, and IPv6 inputs",["pat","policy_nat","destination_nat","static_nat","nat_exemption","nat64"],rejections)
  return {"strategies":strategies,"rejected_alternatives":rejections,"decisions":self.decisions,"assumptions":self.assumptions}
