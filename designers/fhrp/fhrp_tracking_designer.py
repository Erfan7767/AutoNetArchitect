from designers.fhrp.common import FHRPDesigner
class FHRPTrackingDesigner(FHRPDesigner):
 def design(self,r):
  active=int(r.get("active_priority",110));standby=int(r.get("standby_priority",100));default=active-standby+1;objects=[{**x,"decrement":x.get("decrement",default)} for x in r.get("tracking_objects",[])];self.record_decision("tracking",objects,"decrement must force active below standby when failure occurs")
  return {"objects":objects,"bfd_linked":bool(r.get("bfd_enabled")),"decisions":self.decisions}
