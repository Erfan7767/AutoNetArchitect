from designers.nat.common import NATDesigner
class NATVendorMapper(NATDesigner):
 def design(self,r):
  vendor=r.get("vendor","unknown");mapping={"Cisco IOS/IOS-XE":"ip nat inside/outside","Cisco ASA":"manual/twice-NAT order","FortiGate":"central-nat or policy NAT","Palo Alto":"NAT policy pre/post rules","Huawei":"NAT address-group","Juniper":"source/destination/static NAT","MikroTik":"srcnat/dstnat/masquerade"}.get(vendor);self.record_decision("vendor_nat_mapping",mapping,"configuration model feeds later generators")
  return {"vendor":vendor,"mapping":mapping,"status":"mapped" if mapping else "vendor_evidence_required","decisions":self.decisions}
