from designers.interface.common import InterfaceDesigner
class PortMappingMatrixGenerator(InterfaceDesigner):
    """Generate the final cable and port mapping matrix."""
    def design(self,r):
        columns=["interface_name","role","vlan","speed","duplex","poe","description","remote_device","remote_interface","cable_id","status"];rows=[{k:x.get(k) for k in columns} for x in r.get("mappings",[])];self.record_decision("port_matrix",len(rows),"matrix is the source for labeling and as-built documentation");return {"columns":columns,"rows":rows,"json_ready":True,"excel_ready":True,"decisions":self.decisions}
