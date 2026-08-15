from designers.access_control.common import NACDesigner
class DeviceProfilingDesigner(NACDesigner):
 def design(self,r):
  missing=self.mandatory(r,["profiling_server"]);methods=r.get("methods",["dhcp_fingerprint","cdp_lldp","mac_oui"]);self.record_decision("device_profiling",methods,"profiling combines passive signals with explicit server")
  return {"status":"blocked_missing_human_data" if missing else "designed","methods":methods,"profiling_server":r.get("profiling_server"),"warning":"profiling accuracy is probabilistic","decisions":self.decisions,"assumptions":self.assumptions}
