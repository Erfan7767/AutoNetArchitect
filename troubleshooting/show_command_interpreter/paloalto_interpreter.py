"""Vendor-specific bounded show-command interpreter."""

from .vendor_interpreter import VendorShowInterpreter


class PaloAltoInterpreter(VendorShowInterpreter):
    """Interpret common paloalto panos read-only outputs."""

    vendor = "paloalto"
    platform = "panos"
