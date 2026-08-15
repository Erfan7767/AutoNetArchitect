from designers.interface.common import InterfaceDesigner
class InterfaceNamingEngine(InterfaceDesigner):
    """Generate and validate vendor interface names."""
    PREFIXES={"cisco_ios_xe":{"ethernet":"GigabitEthernet","10G":"TenGigabitEthernet","loopback":"Loopback","svi":"Vlan","tunnel":"Tunnel","port_channel":"Port-channel"},"cisco_nxos":{"ethernet":"Ethernet","loopback":"loopback","svi":"Vlan","port_channel":"port-channel"},"juniper":{"1G":"ge","10G":"xe","100G":"et","loopback":"lo0","svi":"irb","port_channel":"ae"},"fortinet":{"ethernet":"port","wan":"wan","management":"mgmt"},"paloalto":{"ethernet":"ethernet1","loopback":"loopback.","tunnel":"tunnel.","svi":"vlan.","port_channel":"ae"},"huawei":{"1G":"GE","10G":"XGE","100G":"100GE","loopback":"LoopBack","svi":"Vlanif","port_channel":"Eth-Trunk"},"aruba":{"ethernet":"1","port_channel":"lag "},"mikrotik":{"ethernet":"ether","10G":"sfp-sfpplus","port_channel":"bonding"}}
    def generate_name(self,r):
        vendor=r.get("platform","cisco_ios_xe");kind=r.get("kind","ethernet");slot=r.get("slot",0);module=r.get("module",0);port=r.get("port",1);number=r.get("number",0);prefix=self.PREFIXES.get(vendor,{}).get(kind)
        if not prefix:return None
        if vendor=="cisco_ios_xe" and kind in {"ethernet","10G"}:return f"{prefix}{slot}/{module}/{port}"
        if vendor=="cisco_nxos" and kind=="ethernet":return f"{prefix}{slot}/{port}"
        if vendor=="juniper" and kind in {"1G","10G","100G"}:return f"{prefix}-{slot}/{module}/{port}"
        if vendor=="fortinet":return f"{prefix}{port}"
        if vendor=="paloalto" and kind=="ethernet":return f"{prefix}/{port}"
        if vendor=="huawei" and kind in {"1G","10G","100G"}:return f"{prefix}{slot}/{module}/{port}"
        if vendor=="aruba" and kind=="ethernet":return f"1/{slot}/{port}"
        if vendor=="mikrotik" and kind=="ethernet":return f"ether{port}"
        return f"{prefix}{number}"
    def design(self,r):
        value=self.generate_name(r);self.record_decision("interface_name",value,"vendor naming convention with explicit model coordinates");return {"name":value,"status":self.model_status(r),"decisions":self.decisions,"assumptions":self.assumptions}
