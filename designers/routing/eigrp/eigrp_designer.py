from designers.base_designer import BaseDesigner
from .eigrp_named_mode_designer import EIGRPNamedModeDesigner
class EIGRPDesigner(BaseDesigner):
 def design(self,requirements):
  if not set(requirements.get("vendors",[])).issubset({"Cisco"}):return {"status":"blocked_vendor_scope","protocol":"eigrp"}
  asn=requirements.get("eigrp_asn");
  if asn is None:self.record_assumption("eigrp_asn","policy_required","ASN must be approved and checked against BGP plan")
  self.record_decision("eigrp_deployment",True,"EIGRP selected by explicit strategy")
  return {"protocol":"eigrp","asn":asn,"named_mode":requirements.get("named_mode",True),"named":EIGRPNamedModeDesigner().design(requirements),"auto_summary":False,"decisions":self.decisions,"assumptions":self.assumptions}
