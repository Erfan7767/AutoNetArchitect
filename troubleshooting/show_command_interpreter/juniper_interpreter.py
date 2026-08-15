"""Vendor-specific bounded show-command interpreter."""

from .vendor_interpreter import VendorShowInterpreter


class JuniperInterpreter(VendorShowInterpreter):
    """Interpret common juniper junos read-only outputs."""

    vendor = "juniper"
    platform = "junos"
