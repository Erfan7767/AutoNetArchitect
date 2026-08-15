from designers.fhrp.common import FHRPDesigner
class FHRPProtocolSelector(FHRPDesigner):
 def design(self,r):
  vendors=set(r.get("vendors",[]));load=bool(r.get("load_balancing",False));multi=bool(r.get("multi_vendor",False));
  if multi:choice,version="vrrp","v3";why="multi-vendor standards-based deployment"
  elif load and vendors=={"Cisco"}:choice,version="glbp","standard";why="Cisco-only load distribution requirement"
  elif vendors=={"Cisco"}:choice,version="hsrp","v2";why="Cisco-only enterprise baseline"
  else:choice,version="vrrp","v3";why="interoperability fallback"
  rejected={"hsrp":"not multi-vendor" if multi else "not selected by policy","vrrp":"not selected by Cisco-only policy" if vendors=={"Cisco"} and not multi and not load else "not selected","glbp":"Cisco proprietary or load balancing not requested" if vendors!={"Cisco"} or not load else "not selected"}
  self.record_decision("fhrp_protocol",{"protocol":choice,"version":version},why,list(rejected),rejected)
  return {"protocol":choice,"version":version,"rationale":why,"rejected_alternatives":rejected,"evidence_status":self.evidence_status(r),"decisions":self.decisions}
