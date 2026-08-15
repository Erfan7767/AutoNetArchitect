from designers.interface.common import InterfaceDesigner
class InterfaceInventoryBuilder(InterfaceDesigner):
    """Build inventory only from supplied platform port maps."""
    def design(self,r):
        self.require_model(r);ports=r.get("platform_port_map",{}).get("ports",[]) if r.get("platform_port_map") else []
        self.record_decision("interface_inventory",len(ports),"inventory is sourced from the equipment model port map")
        return {"device":r.get("device"),"model":r.get("equipment_model"),"ports":ports,"status":self.model_status(r),"decisions":self.decisions,"assumptions":self.assumptions}
