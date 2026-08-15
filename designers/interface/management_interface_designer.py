from designers.interface.common import InterfaceDesigner
class ManagementInterfaceDesigner(InterfaceDesigner):
    """Select dedicated, in-band, or loopback management explicitly."""
    def design(self,r):
        kind=r.get("management_type","dedicated");interface=r.get("management_interface");
        if not interface:self.record_assumption("management_interface",None,"management interface must be supplied or confirmed")
        self.record_decision("management_interface",{"type":kind,"interface":interface},"management path is explicit");return {"type":kind,"interface":interface,"status":"pending" if not interface else "designed","decisions":self.decisions,"assumptions":self.assumptions}
