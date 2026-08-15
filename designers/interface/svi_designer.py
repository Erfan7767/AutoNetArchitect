from designers.interface.common import InterfaceDesigner
class SVIDesigner(InterfaceDesigner):
    """Design routed VLAN interfaces from supplied IP/FHRP data."""
    def design(self,r):
        vendor=r.get("platform","cisco_ios_xe");prefix={"cisco_ios_xe":"Vlan","huawei":"Vlanif","juniper":"irb.","aruba":"vlan "}.get(vendor,"Vlan");svis=[{"interface":f"{prefix}{x['vlan_id']}","vlan_id":x["vlan_id"],"ip":x.get("ip"),"fhrp":x.get("fhrp"),"vrf":x.get("vrf"),"routed":x.get("routed",True)} for x in r.get("vlans",[]) if x.get("routed",True)];self.record_decision("svi_design",svis,"SVIs are created only for routed VLANs");return {"svis":svis,"decisions":self.decisions}
