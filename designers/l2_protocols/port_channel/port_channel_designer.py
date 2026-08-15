from designers.l2_protocols.common import L2Designer
class PortChannelDesigner(L2Designer):
 def design(self,r):
  channels=r.get("channels",[]);self.record_decision("port_channels",channels,"LAGs follow topology and redundancy intent")
  return {"channels":channels,"evidence_status":self.evidence_status(r),"decisions":self.decisions}
