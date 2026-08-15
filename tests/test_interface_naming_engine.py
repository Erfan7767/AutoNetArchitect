from designers.interface.interface_naming_engine import InterfaceNamingEngine
def test_cisco_name(): assert InterfaceNamingEngine().generate_name({"platform":"cisco_ios_xe","kind":"10G","slot":1,"module":0,"port":1})=="TenGigabitEthernet1/0/1"
