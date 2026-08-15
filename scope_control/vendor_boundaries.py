"""Vendor scope boundaries."""
class VendorBoundaries:
    """Keep V1 vendor scope explicit."""
    SUPPORTED = {"Huawei"}
    def check(self, vendor: str) -> dict[str, object]:
        """Return vendor support status."""
        return {"status": "supported" if vendor in self.SUPPORTED else "unsupported", "vendor": vendor, "required_action": "validated vendor evidence" if vendor not in self.SUPPORTED else "none"}
