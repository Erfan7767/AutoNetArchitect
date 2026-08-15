from designers.access_control.common import NACDesigner
class Dot1XExceptionPolicy(NACDesigner):
 def design(self,r):
  exceptions=r.get("exceptions",[]);valid=all(x.get("device") and x.get("reason") and x.get("approver") and x.get("expiry") and x.get("controls") for x in exceptions);self.record_decision("dot1x_exceptions",len(exceptions),"exceptions require owner, expiry, approval, and compensating controls");return {"status":"designed" if valid else "blocked_incomplete_exception","exceptions":exceptions,"decisions":self.decisions}
