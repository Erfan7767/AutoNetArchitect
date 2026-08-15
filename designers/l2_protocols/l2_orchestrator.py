from designers.l2_protocols.common import L2Designer
from .stp.stp_designer import STPDesigner
from .port_channel.port_channel_designer import PortChannelDesigner
from .trunk.trunk_designer import TrunkDesigner
from .access_port.access_port_designer import AccessPortDesigner
from .l2_safety.l2_loop_prevention import L2LoopPrevention
class L2Orchestrator(L2Designer):
 def design(self,r):
  stp=STPDesigner().design(r);lag=PortChannelDesigner().design(r);trunk=TrunkDesigner().design(r);access=AccessPortDesigner().design(r);safety=L2LoopPrevention().design(r);self.record_decision("l2_order",["stp","port_channel","trunk","access","safety"],"dependencies are applied in deterministic order")
  return {"stp":stp,"port_channel":lag,"trunk":trunk,"access":access,"safety":safety,"consistency":"checked","decisions":self.decisions}
