from designers.interface.common import InterfaceDesigner
class InterfaceDescriptionGenerator(InterfaceDesigner):
    """Generate mandatory interface descriptions."""
    def design(self,r):
        rows=[]
        for x in r.get("mappings",[]):rows.append({**x,"description":f"{x.get('role','UNKNOWN')}:{x.get('remote_device','UNKNOWN')}:{x.get('remote_interface','UNKNOWN')}:{x.get('cable_id','UNKNOWN')}"})
        self.record_decision("interface_descriptions",len(rows),"uniform role/remote/cable format");return {"mappings":rows,"all_described":all(bool(x.get("description")) for x in rows),"decisions":self.decisions}
