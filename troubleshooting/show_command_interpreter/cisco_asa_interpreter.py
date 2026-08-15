"""Vendor-specific bounded show-command interpreter."""

from .vendor_interpreter import VendorShowInterpreter


class CiscoASAInterpreter(VendorShowInterpreter):
    """Interpret common cisco asa read-only outputs."""

    vendor = "cisco"
    platform = "asa"
