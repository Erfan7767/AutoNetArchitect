from designers.l2_protocols.common import L2Designer
class LoadBalanceSelector(L2Designer):
 def design(self,r):
  method=r.get("load_balance","src-dst-ip");self.record_decision("load_balance",method,"IP hash is the conservative cross-platform baseline")
  return {"method":method,"distribution_effectiveness":"requires traffic evidence","decisions":self.decisions}
