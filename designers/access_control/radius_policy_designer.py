from designers.access_control.common import NACDesigner
class RadiusPolicyDesigner(NACDesigner):
 def design(self,r):
  policies={"employee":{"vlan":r.get("employee_vlan"),"access":"full"},"contractor":{"vlan":r.get("contractor_vlan"),"access":"restricted"},"guest":{"vlan":r.get("guest_vlan"),"access":"internet_only"},"device":{"vlan":r.get("device_vlan"),"access":"device_specific"},"unknown":{"vlan":r.get("quarantine_vlan"),"access":"quarantine"}};self.record_decision("radius_policy",policies,"identity maps to VLAN/ACL/SGT and session controls")
  return {"policies":policies,"server_configuration":"HumanSuppliedMandatory","decisions":self.decisions}
