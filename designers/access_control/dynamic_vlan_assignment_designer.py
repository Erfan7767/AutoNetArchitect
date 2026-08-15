from designers.access_control.common import NACDesigner
class DynamicVLANAssignmentDesigner(NACDesigner):
 def design(self,r):
  vlans=r.get("dynamic_vlans",[]);missing=[v for v in vlans if v not in r.get("available_vlans",[])];self.record_decision("dynamic_vlan",vlans,"RADIUS tunnel attributes assign only existing VLANs")
  return {"status":"blocked_vlan_missing" if missing else "designed","radius_attributes":["Tunnel-Type=VLAN","Tunnel-Medium-Type=802","Tunnel-Private-Group-ID"],"vlans":vlans,"missing_vlans":missing,"fallbacks":r.get("fallbacks",{}),"decisions":self.decisions}
