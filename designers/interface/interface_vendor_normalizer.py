from designers.interface.common import InterfaceDesigner
class InterfaceVendorNormalizer(InterfaceDesigner):
    """Normalize and render interface identities across vendors."""
    def normalize(self,r):
        """Return normalized type/speed/coordinates."""
        return {"type":r.get("type","ethernet"),"speed":r.get("speed"),"slot":r.get("slot"),"module":r.get("module"),"port":r.get("port")}
    def design(self,r):
        normalized=self.normalize(r);self.record_decision("interface_normalization",normalized,"normalized identity supports reconciliation and migration");return {"normalized":normalized,"vendor_name":r.get("vendor_name"),"decisions":self.decisions}
