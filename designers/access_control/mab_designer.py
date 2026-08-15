from designers.access_control.common import NACDesigner
class MABDesigner(NACDesigner):
 def design(self,r):
  fmt=r.get("mac_format","lowercase-colon");self.record_decision("mab",r.get("device_types",["printer","camera","iot"]),"MAB is fallback for devices without supplicants")
  return {"device_types":r.get("device_types",["printer","camera","iot"]),"mac_format":fmt,"database":r.get("database","central_nac"),"warning":"MAC spoofing risk; use port security and DHCP snooping","decisions":self.decisions}
