"""IP addressing and summarization designer."""
from designers.base_designer import BaseDesigner
class IPDesigner(BaseDesigner):
    """Design loopbacks, summaries, growth reserves, and brownfield-safe allocations."""
    def design(self,requirements):
        growth=float(requirements.get("growth_percent",20));brownfield=bool(requirements.get("brownfield",False));
        if "growth_percent" not in requirements:self.record_assumption("growth_percent",growth,"default reserve; validate with owner")
        summary=requirements.get("summary_prefix","10.0.0.0/8");loopbacks=requirements.get("loopback_prefix","10.255.0.0/16")
        self.record_decision("addressing",{"summary":summary,"loopbacks":loopbacks,"growth_percent":growth},"supports summarization and future allocation",["flat addressing"],{})
        return {"summary_prefix":summary,"loopback_prefix":loopbacks,"growth_percent":growth,"brownfield":brownfield,"decisions":self.decisions,"assumptions":self.assumptions}
