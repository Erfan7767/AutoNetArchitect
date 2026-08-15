from designers.base_designer import BaseDesigner
class ConvergenceOptimizer(BaseDesigner):
 def design(self,requirements):
  proposals=[]
  if not requirements.get("bfd_enabled"):proposals.append("evaluate BFD")
  if requirements.get("detection_ms",1000)<100:proposals.append("review aggressive detection timers")
  self.record_decision("convergence_optimization",proposals,"proposals are guarded by timer safety review")
  return {"proposals":proposals,"warning":bool(requirements.get("detection_ms",1000)<100),"decisions":self.decisions}
