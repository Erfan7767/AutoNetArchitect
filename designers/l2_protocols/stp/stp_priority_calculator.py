from designers.l2_protocols.common import L2Designer
class STPPriorityCalculator(L2Designer):
 def design(self,r):
  priorities={"root":4096,"secondary":8192,"distribution":16384,"access":32768}; self.record_decision("stp_priorities",priorities,"deterministic root election policy")
  return {"priorities":priorities,"vlan_offset":r.get("vlan_offset",True),"decisions":self.decisions}
