"""Vendor-specific bounded show-command interpreter."""

from .vendor_interpreter import VendorShowInterpreter


class ArubaInterpreter(VendorShowInterpreter):
    """Interpret common aruba aoscx read-only outputs."""

    vendor = "aruba"
    platform = "aoscx"
