from designers.fhrp.common import FHRPDesigner
class FHRPAuthenticationDesigner(FHRPDesigner):
 def design(self,r):
  protocol=r.get("protocol","hsrp");method=r.get("method","md5-key-string") if protocol=="hsrp" else r.get("method","text");limitation="VRRPv3 has no native authentication" if protocol=="vrrp" and r.get("version","v3")=="v3" else None;self.record_decision("fhrp_authentication",method,"secret storage and protocol capability policy")
  return {"protocol":protocol,"method":method,"secrets_manager":r.get("secrets_manager",True),"limitation":limitation,"decisions":self.decisions}
