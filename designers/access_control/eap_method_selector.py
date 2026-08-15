from designers.access_control.common import NACDesigner
class EAPMethodSelector(NACDesigner):
 def design(self,r):
  method="eap-tls" if r.get("pki_available") else "peap";self.record_decision("eap_method",method,"PKI availability and device ownership determine EAP method")
  return {"method":method,"pki_required":method=="eap-tls","server_certificate_required":True,"decisions":self.decisions}
