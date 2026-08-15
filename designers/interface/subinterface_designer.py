from designers.interface.common import InterfaceDesigner
class SubinterfaceDesigner(InterfaceDesigner):
    """Design tagged subinterfaces from parent and VLAN inputs."""
    def design(self,r):
        subs=[{"parent":x.get("parent"),"interface":f"{x.get('parent')}.{x['vlan_id']}","encapsulation":"dot1q","vlan_id":x["vlan_id"],"ip":x.get("ip"),"description":x.get("description")} for x in r.get("subinterfaces",[])];self.record_decision("subinterfaces",subs,"dot1q subinterfaces require explicit parent and VLAN");return {"subinterfaces":subs,"decisions":self.decisions}
