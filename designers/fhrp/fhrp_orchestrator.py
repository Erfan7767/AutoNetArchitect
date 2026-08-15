from designers.fhrp.common import FHRPDesigner
from .fhrp_protocol_selector import FHRPProtocolSelector
from .hsrp_designer import HSRPDesigner
from .vrrp_designer import VRRPDesigner
from .glbp_designer import GLBPDesigner
from .fhrp_vip_planner import FHRPVIPPlanner
from .fhrp_priority_designer import FHRPPriorityDesigner
from .fhrp_stp_alignment_enforcer import FHRPSTPAlignmentEnforcer
class FHRPOrchestrator(FHRPDesigner):
 def design(self,r):
  selection=FHRPProtocolSelector().design(r);protocol=selection["protocol"];vip=FHRPVIPPlanner().design(r);base={**r,"vlans":[{**v,"virtual_ip":next((p["vip"] for p in vip["plans"] if p["subnet"]==v.get("subnet")),v.get("virtual_ip"))} for v in r.get("vlans",[])]}
  artifact=HSRPDesigner().design(base) if protocol=="hsrp" else VRRPDesigner().design(base) if protocol=="vrrp" else GLBPDesigner().design(base);alignment=FHRPSTPAlignmentEnforcer().design(r);priority=FHRPPriorityDesigner().design({"vlan_ids":[v.get("vlan_id") for v in r.get("vlans",[])]});self.record_decision("fhrp_orchestration",protocol,"selector then per-VLAN design, priority, and STP alignment")
  return {"selection":selection,"vip":vip,"artifact":artifact,"priority":priority,"alignment":alignment,"status":"blocked_alignment" if not alignment["aligned"] else "designed","decisions":self.decisions}
