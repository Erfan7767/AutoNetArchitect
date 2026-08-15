from designers.interface.common import InterfaceDesigner
class InterfaceSpeedNegotiation(InterfaceDesigner):
    """Select speed and negotiation behavior by interface role."""
    def design(self,r):
        role=r.get("role","access");auto=role not in {"uplink","wan"};speed=r.get("speed","auto");self.record_decision("speed_negotiation",{"speed":speed,"duplex":"auto" if auto else "full","auto_negotiation":auto},"uplinks use explicit speed while access ports negotiate");return {"speed":speed,"duplex":"auto" if auto else "full","auto_negotiation":auto,"remote_compatibility_required":True,"decisions":self.decisions}
