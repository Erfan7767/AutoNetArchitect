from designers.access_control.common import NACDesigner
class NACVendorMapper(NACDesigner):
 MAP={"cisco_ios_xe":["aaa new-model","aaa authentication dot1x","dot1x system-auth-control","authentication port-control auto","authentication order dot1x mab","mab"],"cisco_nxos":["feature dot1x","radius-server host"],"huawei":["dot1x enable","dot1x authentication-method eap"],"aruba":["aaa authentication port-access dot1x authenticator","aaa authentication port-access mac-auth"],"juniper":["dot1x authenticator interface","server-reject-vlan","guest-vlan"],"fortigate":["FortiNAC integration","switch-controller managed-switch"],"mikrotik":["/interface dot1x server","/radius add"]}
 def design(self,r):
  vendor=r.get("vendor");commands=self.MAP.get(vendor);self.record_decision("nac_vendor_mapping",vendor,"vendor mapping feeds later configuration generators");return {"vendor":vendor,"commands":commands,"status":"mapped" if commands else "vendor_evidence_required","decisions":self.decisions}
