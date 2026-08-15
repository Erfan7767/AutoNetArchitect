from designers.nat.common import NATDesigner
class NATExemptionDesigner(NATDesigner):
 def design(self,r):
  rules=[{"source":x.get("source"),"destination":x.get("destination"),"order":i+1,"action":"no-nat","reason":x.get("reason","VPN or inter-segment traffic")} for i,x in enumerate(r.get("vpn_flows",[]))];self.record_decision("nat_exemption",rules,"exemptions are ordered before translation rules")
  return {"rules":rules,"ordered_before_nat":True,"vendor_notes":{"Cisco":"route-map deny in ACL","FortiGate":"central-nat or policy exemption","PaloAlto":"no-NAT policy"},"decisions":self.decisions}
