from designers.l2_protocols.common import L2Designer
class STPTuning(L2Designer):
 def design(self,r):
  timers=r.get("timers",{"hello":2,"forward_delay":15,"max_age":20}); self.record_decision("stp_timers",timers,"defaults retained unless explicit evidence justifies tuning")
  return {"timers":timers,"portfast_access":True,"portfast_trunk":bool(r.get("virtualization_trunk",False)),"warning":"timer changes require evidence" if "timers" in r else None,"decisions":self.decisions}
