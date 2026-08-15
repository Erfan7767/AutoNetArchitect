from designers.l2_protocols.common import L2Designer
from .stp_mode_selector import STPModeSelector
from .stp_root_designer import STPRootDesigner
class STPDesigner(L2Designer):
 def design(self,r):
  mode=STPModeSelector().design(r); roots=STPRootDesigner().design(r); self.record_decision("stp_deployment",mode["mode"],"STP is designed before LAG and trunks")
  return {"mode":mode,"roots":roots,"decisions":self.decisions,"evidence_status":self.evidence_status(r)}
