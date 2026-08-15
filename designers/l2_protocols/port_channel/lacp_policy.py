from designers.l2_protocols.common import L2Designer
class LACPPolicy(L2Designer):
 def design(self,r):
  policy={"mode":"active/active","rate":r.get("lacp_rate","normal"),"min_links":r.get("min_links",1)};self.record_decision("lacp_policy",policy,"active LACP avoids silent static-LAG failure")
  return {"policy":policy,"static_lag_warning":True,"decisions":self.decisions}
