from designers.base_designer import BaseDesigner
class OSPFSummarizationPlanner(BaseDesigner):
 def design(self,requirements):
  summaries=requirements.get("area_summaries",[]);self.record_decision("ospf_summarization",summaries,"summaries only where IP plan supplies area prefixes")
  return {"summaries":summaries,"discard_route_review":True,"decisions":self.decisions}
