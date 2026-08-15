from designers.base_designer import BaseDesigner
class BFDDesigner(BaseDesigner):
 def design(self,requirements):
  links=requirements.get("links",[]);self.record_decision("bfd_scope",links,"enable on supported routing adjacencies and tracked static paths")
  return {"enabled_links":links,"min_tx_ms":requirements.get("min_tx_ms",300),"min_rx_ms":requirements.get("min_rx_ms",300),"multiplier":requirements.get("multiplier",3),"evidence_required":not bool(requirements.get("evidence_ids")),"decisions":self.decisions}
